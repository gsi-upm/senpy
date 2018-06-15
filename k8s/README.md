Deploy senpy to a kubernetes cluster.
The files are templates, which need to be expanded with something like envsubst.

Example usage:

```
cat k8s/*.ya*ml | envsubst | kubectl apply -n senpy -f -
```
