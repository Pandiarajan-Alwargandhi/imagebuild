#!/bin/sh
set -x

# Authenticate with Azure
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $TENANT_ID
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME --file $KUBECONFIG_FILE

# Create Namespace if not exists
if ! kubectl --kubeconfig=$KUBECONFIG_FILE get namespace ${KUBE_NAMESPACE}; then
    kubectl --kubeconfig=$KUBECONFIG_FILE create namespace ${KUBE_NAMESPACE}
fi

# Deploy to AKS
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f job.yaml -n ${KUBE_NAMESPACE}
