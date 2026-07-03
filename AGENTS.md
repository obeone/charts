# Contributor Guide

## Testing rules

- Si tu changes quoi que ce soit dans Chart.yaml, il faut lancer `helm dep up` pour mettre à jour le fichier de dépendances.
- Quelque soit les modifications apportées, il faudr toujours lancer `helm lint` sur le chart modifié et corriger les erreurs qui apparaissent avant de committer.

## Documentation

- Les `README.md` des charts sont générés par helm-docs : ne jamais les éditer à la main. Modifier `charts/_templates.gotmpl` (squelette commun) ou le `README.md.gotmpl` du chart concerné, puis régénérer depuis la racine du dépôt :

  ```shell
  helm-docs --chart-search-root=charts --template-files=./_templates.gotmpl --template-files=README.md.gotmpl
  ```

- Après toute modification de `values.yaml` (les commentaires `# --` alimentent la table Values) ou de `Chart.yaml` (version, description), relancer helm-docs pour que le `README.md` reste synchronisé, et committer le README régénéré avec le reste.
