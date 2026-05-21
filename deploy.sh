#!/bin/bash

# Exit on any error
set -e

# Check for required tools

if ! command -v curl &> /dev/null; then
    echo "Curl not found. Installing Curl..."
    sudo apt-get update
    sudo apt-get install curl
fi

if ! command -v python3 &> /dev/null; then
    echo "Python not found. Installing Python..."
    sudo apt-get update
    sudo apt-get install -y python3
fi

if ! command -v pip &> /dev/null; then
    echo "pip not found. Installing pip..."
    wget https://bootstrap.pypa.io/get-pip.py
    sudo python3 get-pip.py --break-system-packages

fi

if ! command -v docker &> /dev/null; then
    echo "Docker not installed. Installing Docker..."
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
fi

if ! command -v kubectl &> /dev/null; then
    echo "Kubectl not installed. Installing Kubectl..."
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
    sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list
    sudo apt-get update
    sudo apt-get install -y kubectl kubeadm kubelet
fi

if ! command -v kind &> /dev/null; then
    echo "Kind not installed. Installing Kind..."
    [ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Prompt for environment variable configuration
if [ ! -f .env ]; then
    echo ".env file not found in the root directory. Please create it with the necessary variables."
    echo "MONGO_URI=your_mongo_uri"
    echo "SECRET_KEY=your_secret_key"
    exit 1
    exit 1
fi

# Step 0.1: Copy the .env file to each microservice
echo "Copying .env file to each microservice..."
cp .env ./microservices/authentication/.env
cp .env ./microservices/scoring/.env
cp .env ./microservices/settings/.env
echo ".env file copied successfully."

echo "Starting SaaS deployment..."

# Step 1: Create a Kind cluster
echo "Creating Kind cluster..."
sudo kind create cluster --name mycluster --config kubernetes/cluster-config.yml

echo "Kind cluster created successfully."

# Step 2: Deploy NGINX Ingress Controller
echo "Deploying NGINX Ingress Controller..."
sudo kubectl apply -f kubernetes/deploy.yaml

# Wait for the ingress controller to be ready
sudo kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=90s

echo "NGINX Ingress Controller deployed successfully."

# Step 3: Build and Load Docker Images into Kind
echo "Building and loading Docker images into Kind..."

# # Build and load the authentication service
# sudo docker build -t authentication ./microservices/authentication
# sudo kind load docker-image authentication

# # Build and load the scoring service
# sudo docker build -t scoring ./microservices/scoring
# sudo kind load docker-image scoring

# # Build and load the settings service
# sudo docker build -t settings ./microservices/settings
# sudo kind load docker-image settings

echo "Loading Docker image 'authentication' into Kind..."
docker build -t authentication ./microservices/authentication
kind load docker-image authentication --name mycluster
while [ $? -ne 0 ]; do
    echo "Retrying Docker image load..."
    sleep 5
    kind load docker-image authentication --name mycluster
done
echo "Docker image 'authentication' loaded successfully."


echo "Loading Docker image 'scoring' into Kind..."
docker build -t scoring ./microservices/scoring
kind load docker-image scoring --name mycluster
while [ $? -ne 0 ]; do
    echo "Retrying Docker image load..."
    sleep 5
    kind load docker-image scoring --name mycluster
done
echo "Docker image 'scoring' loaded successfully."


echo "Loading Docker image 'settings' into Kind..."
docker build -t settings ./microservices/settings
kind load docker-image settings --name mycluster
while [ $? -ne 0 ]; do
    echo "Retrying Docker image load..."
    sleep 5
    kind load docker-image settings --name mycluster
done
echo "Docker image 'settings' loaded successfully."


echo "Docker images loaded successfully."

# Step 4: Deploy Microservices
echo "Deploying microservices..."
sudo kubectl apply -f kubernetes/authentication-app.yaml
sudo kubectl apply -f kubernetes/scoring-app.yaml
sudo kubectl apply -f kubernetes/settings-app.yaml
echo "Microservices deployed successfully."

# Step 5: Deploy Ingress Rules
echo "Deploying Ingress rules..."
sudo kubectl apply -f kubernetes/microservices-ingress.yaml

echo "Ingress rules deployed successfully."

# Step 6: Forward controller port to machine
sudo kubectl port-forward svc/ingress-nginx-controller 8080:80 -n ingress-nginx

echo "Deployment complete. Your SaaS is ready and accessible via the following endpoints:"
echo "Authentication Service: http://localhost:8080/authentication/docs"
echo "Scoring Service: http://localhost/score:8080/docs"
echo "Settings Service: http://localhost:8080/settings/docs"
