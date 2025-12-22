# Kubernetes Essentials Guide

## What is Kubernetes?

Kubernetes (K8s) is an open-source container orchestration platform that automates the deployment, scaling, and management of containerized applications. Originally developed by Google, it's now maintained by the Cloud Native Computing Foundation (CNCF).

## Core Concepts

### Pods
The smallest deployable unit in Kubernetes. A Pod represents a single instance of a running process and can contain one or more containers that share storage and network resources.

**Key Points**:
- Pods are ephemeral and can be created/destroyed dynamically
- Containers in a Pod share the same IP address and port space
- Used for tightly coupled applications that need to share resources

### Deployments
Manages the deployment and scaling of Pods. Deployments ensure the desired number of Pod replicas are running and handles rolling updates.

**Features**:
- Automatic rollback on failure
- Rolling updates with zero downtime
- Declarative updates to applications
- Self-healing capabilities

### Services
An abstract way to expose an application running on Pods as a network service. Services provide stable networking and load balancing.

**Types**:
1. **ClusterIP**: Default, exposes service internally
2. **NodePort**: Exposes service on each Node's IP at a static port
3. **LoadBalancer**: Creates external load balancer (cloud provider)
4. **ExternalName**: Maps service to DNS name

### ConfigMaps and Secrets
- **ConfigMaps**: Store non-sensitive configuration data as key-value pairs
- **Secrets**: Store sensitive information (passwords, tokens, keys) encoded in base64

### Namespaces
Virtual clusters within a physical cluster. Used to divide cluster resources between multiple users or teams.

**Common Namespaces**:
- `default`: Default namespace for objects
- `kube-system`: Kubernetes system components
- `kube-public`: Publicly readable resources
- `kube-node-lease`: Node heartbeat data

## Architecture

### Control Plane Components

**API Server** (`kube-apiserver`):
- Front-end for the Kubernetes control plane
- Exposes the Kubernetes API
- Validates and processes REST requests

**etcd**:
- Consistent and highly-available key-value store
- Stores all cluster data
- Backup etcd regularly!

**Scheduler** (`kube-scheduler`):
- Assigns Pods to Nodes
- Considers resource requirements, constraints, and policies

**Controller Manager** (`kube-controller-manager`):
- Runs controller processes
- Node controller, Replication controller, Endpoints controller

### Node Components

**kubelet**:
- Agent running on each Node
- Ensures containers are running in Pods
- Reports Node and Pod status to API server

**kube-proxy**:
- Network proxy on each Node
- Maintains network rules for Pod communication
- Implements Service abstraction

**Container Runtime**:
- Software responsible for running containers
- Examples: Docker, containerd, CRI-O

## Common kubectl Commands

```bash
# Cluster Information
kubectl cluster-info
kubectl get nodes
kubectl get namespaces

# Working with Pods
kubectl get pods
kubectl get pods -n <namespace>
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl exec -it <pod-name> -- /bin/bash

# Deployments
kubectl get deployments
kubectl create deployment nginx --image=nginx
kubectl scale deployment nginx --replicas=3
kubectl rollout status deployment/nginx
kubectl rollout undo deployment/nginx

# Services
kubectl get services
kubectl expose deployment nginx --port=80 --type=LoadBalancer
kubectl describe service nginx

# ConfigMaps and Secrets
kubectl create configmap app-config --from-file=config.properties
kubectl create secret generic db-secret --from-literal=password=mypass
kubectl get configmaps
kubectl get secrets

# Apply YAML manifests
kubectl apply -f deployment.yaml
kubectl delete -f deployment.yaml

# Debugging
kubectl get events
kubectl top nodes
kubectl top pods
```

## Best Practices

### 1. Resource Management
Always set resource requests and limits:
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "250m"
  limits:
    memory: "128Mi"
    cpu: "500m"
```

### 2. Health Checks
Implement liveness and readiness probes:
- **Liveness**: Determines if container should be restarted
- **Readiness**: Determines if Pod is ready to receive traffic

### 3. Use Labels and Selectors
Organize resources with meaningful labels:
```yaml
labels:
  app: myapp
  tier: frontend
  environment: production
```

### 4. Security
- Run containers as non-root users
- Use Pod Security Policies
- Enable RBAC (Role-Based Access Control)
- Scan container images for vulnerabilities
- Use network policies to control traffic

### 5. High Availability
- Run multiple replicas for critical services
- Use Pod Disruption Budgets
- Distribute workloads across multiple zones
- Implement proper backup strategies

### 6. Configuration Management
- Use ConfigMaps for configuration
- Store secrets in Secret objects (or external vault)
- Never hardcode configuration in container images
- Use Helm for complex deployments

### 7. Monitoring and Logging
- Implement centralized logging (ELK, Loki)
- Use Prometheus for metrics collection
- Set up alerts for critical events
- Monitor resource usage and optimize

## Common Deployment Patterns

### Blue-Green Deployment
Maintain two identical environments (blue and green). Switch traffic from one to another for zero-downtime deployments.

### Canary Deployment
Gradually roll out changes to a small subset of users before full deployment.

### Rolling Update
Default Kubernetes strategy. Gradually replaces old Pods with new ones.

## Troubleshooting Tips

1. **Pod not starting**: Check events with `kubectl describe pod`
2. **Image pull errors**: Verify image name and registry credentials
3. **CrashLoopBackOff**: Check logs with `kubectl logs`
4. **Service not accessible**: Verify service selectors match Pod labels
5. **Resource issues**: Check node capacity with `kubectl top nodes`

## Learning Resources

- Official Kubernetes Documentation: kubernetes.io/docs
- Kubernetes Patterns book by Bilgin Ibryam
- CNCF Certified Kubernetes Administrator (CKA) certification
- Practice with Minikube or kind for local development

## Conclusion

Kubernetes is powerful but complex. Start with basic concepts, practice with simple deployments, and gradually explore advanced features. The container orchestration capabilities make it invaluable for modern cloud-native applications.
