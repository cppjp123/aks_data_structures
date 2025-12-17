import subprocess
import os
import time
import sys
import json

# --- Path Setup to import 'utils' from parent directory ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.logger import Logger

# --- Configuration ---
PROJECT_ROOT = parent_dir
K8S_DIR = os.path.join(PROJECT_ROOT, "k8s")
TERRAFORM_DIR = os.path.join(PROJECT_ROOT, "terraform", "local")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "driver", "config.json")


class InfrastructureManager:
    def __init__(self):
        self.env = os.environ.copy()
        self.config = self.load_config()
        self.services = self.discover_services()
        self.minikube_ip = None

    def load_config(self):
        """Loads configuration from config.json"""
        if not os.path.exists(CONFIG_FILE):
            Logger.error(f"Config file not found at: {CONFIG_FILE}")
            sys.exit(1)

        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            Logger.error(f"Failed to parse config.json: {e}")
            sys.exit(1)

    def discover_services(self):
        services = []
        for name in os.listdir(PROJECT_ROOT):
            path = os.path.join(PROJECT_ROOT, name)
            if os.path.isdir(path) and os.path.isfile(os.path.join(path, "Dockerfile")):
                services.append(name)
        return services

    def run_cmd(self, cmd, shell=False, capture=True, cwd_override=None, ignore_errors=False):
        """Helper to run shell commands."""
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        Logger.debug(f"Exec: {cmd_str}")

        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                check=True,
                stdout=subprocess.PIPE if capture else None,
                stderr=subprocess.PIPE if capture else None,
                env=self.env,
                cwd=cwd_override or PROJECT_ROOT,
                text=True,
            )
            return result.stdout.strip() if capture else ""
        except subprocess.CalledProcessError as e:
            if ignore_errors:
                return ""
            Logger.error(f"Command failed: {cmd_str}")
            if capture and e.stderr:
                print(e.stderr)
            sys.exit(1)

    # ---------------- Cleanup & Unlock Logic ---------------- #

    def force_unlock_terraform(self):
        """Removes the lock file if it exists."""
        lock_file = os.path.join(TERRAFORM_DIR, ".terraform.tfstate.lock.info")
        if os.path.exists(lock_file):
            Logger.warning(f"Found Terraform Lock File: {lock_file}")
            try:
                os.remove(lock_file)
                Logger.success("Removed Lock File. Terraform is now unlocked.")
            except Exception as e:
                Logger.error(f"Could not remove lock file: {e}")

    def cleanup_resources(self):
        Logger.header("Step 0: Cleaning Up Old Resources")
        Logger.info("Force deleting all deployments, services, and ingress...")

        self.run_cmd(["kubectl", "delete", "deployments,services,ingress,configmaps", "--all"], ignore_errors=True)
        # Force delete namespace to reload permissions defined in yaml
        self.run_cmd(["kubectl", "delete", "namespace", self.config["ingress"]["namespace"]], ignore_errors=True)

        Logger.info("Waiting 5 seconds for resources to terminate...")
        time.sleep(5)
        Logger.success("Cleanup complete.")

    # ---------------- Standard Logic ---------------- #

    def check_minikube(self):
        Logger.header("Step 1: Checking Infrastructure")
        try:
            result = subprocess.run(["minikube", "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0 and "Running" in result.stdout:
                Logger.success("Minikube is running.")
            else:
                Logger.warning("Starting Minikube...")
                subprocess.run(["minikube", "start"], check=True)
        except Exception as e:
            Logger.error(f"Minikube check failed: {e}")
            sys.exit(1)

        try:
            ip = subprocess.check_output(["minikube", "ip"], text=True).strip()
            self.minikube_ip = ip
            Logger.info(f"Minikube IP: {ip}")
        except:
            self.minikube_ip = "<minikube-ip>"

    def set_docker_env(self):
        Logger.header("Step 2: Configuring Docker Environment")
        try:
            output = subprocess.check_output(["minikube", "-p", "minikube", "docker-env", "--shell", "powershell"],
                                             text=True)
            for line in output.splitlines():
                if line.strip().startswith("$Env:DOCKER_HOST"):
                    self.env["DOCKER_HOST"] = line.split("=", 1)[1].strip().strip('"')
                elif line.strip().startswith("$Env:DOCKER_TLS_VERIFY"):
                    self.env["DOCKER_TLS_VERIFY"] = line.split("=", 1)[1].strip().strip('"')
                elif line.strip().startswith("$Env:DOCKER_CERT_PATH"):
                    self.env["DOCKER_CERT_PATH"] = line.split("=", 1)[1].strip().strip('"')
            Logger.info(f"Docker pointed to Minikube: {self.env.get('DOCKER_HOST')}")
        except:
            Logger.error("Failed to configure Docker env")

    def build_images(self):
        Logger.header("Step 4: Building Service Images")
        for service in self.services:
            Logger.info(f"Building: {service}...")
            self.run_cmd(["docker", "build", "-t", f"{service}-service:latest", f"./{service}"])
        Logger.success("Images built.")

    def deploy_k8s(self):
        Logger.header("Step 5: Deploying via Terraform")
        self.run_cmd(["terraform", "init"], cwd_override=TERRAFORM_DIR, capture=False)
        self.run_cmd(["terraform", "apply", "-auto-approve"], cwd_override=TERRAFORM_DIR, capture=False)
        Logger.success("Terraform apply completed.")

    def wait_for_pods(self):
        Logger.header("Step 6: Health Check")
        retries = 0
        while retries < 40:
            output = self.run_cmd(["kubectl", "get", "pods"])
            if "Running" in output and "Error" not in output and "CrashLoop" not in output and "ContainerCreating" not in output:
                if "backend" in output and "ui" in output:
                    Logger.success("All Pods are RUNNING!")
                    return
            time.sleep(3)
            retries += 1
            if retries % 5 == 0: Logger.debug("Waiting for pods...")
        Logger.warning("Timed out waiting for pods.")

    def open_tunnel(self):
        # Load values directly from the config object
        local_port = self.config["ingress"]["local_port"]
        container_port = self.config["ingress"]["container_port"]
        namespace = self.config["ingress"]["namespace"]
        service = self.config["ingress"]["service_name"]

        Logger.header("Step 8: Opening Access Tunnel")
        Logger.info(f"Starting port-forwarding to Ingress ({service})")
        Logger.info(f"Mapping: localhost:{local_port} -> Container:{container_port}")
        Logger.info(f"Access URL: http://localhost:{local_port}")
        Logger.info("Press Ctrl+C to stop.")

        try:
            subprocess.run([
                "kubectl", "port-forward",
                "-n", namespace,
                f"svc/{service}",
                f"{local_port}:{container_port}"
            ], check=True)
        except KeyboardInterrupt:
            Logger.info("\nGoodbye!")

    def main(self):
        self.force_unlock_terraform()
        self.cleanup_resources()
        self.check_minikube()
        self.set_docker_env()
        self.build_images()
        self.deploy_k8s()
        self.wait_for_pods()
        self.open_tunnel()


if __name__ == "__main__":
    manager = InfrastructureManager()
    manager.main()
