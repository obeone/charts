# Contributor Guide

## Testing rules

- Si tu changes quoi que ce soit dans Chart.yaml, il faut lancer `helm dep up` pour mettre à jour le fichier de dépendances.
- Quelque soit les modifications apportées, il faudr toujours lancer `helm lint` sur le chart modifié et corriger les erreurs qui apparaissent avant de committer.
