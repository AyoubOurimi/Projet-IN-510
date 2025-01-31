# Projet IN-520

## Description
Ce projet a pour objectif d'analyser et de générer des résultats à partir de grammaires formelles. Les principaux scripts Python permettent de travailler avec des formats tels que les formes de Chomsky et de Greibach. Un Makefile est fourni pour automatiser les tâches.

---

## Structure du projet

### Fichiers principaux
- **`Grammaire.py`** : Script Python qui analyse une grammaire donnée.
- **`Generer.py`** : Génère des fichiers de résultats selon les formats de grammaires spécifiés.

### Fichiers d'entrée
- **`exemple.general`** :
- **`exemple2.general`** 
- **`exemple3.general`** 


### Fichiers générés
- **Résultats des générateurs** :
  - `exemple.chomsky` | `exemple.greibach`
  - `exemple2.chomsky` | `exemple2.greibach`
  - `exemple3.chomsky` | `exemple3.greibach`
---

## Prérequis

### Logiciels nécessaires
1. **Python 3.x** :
   - Téléchargez Python depuis [python.org](https://www.python.org/).
   - Assurez-vous que Python est accessible depuis votre terminal en vérifiant la version :
     ```bash
     python --version
     ```
2. **Make** (facultatif) :
   - Sous Windows, installez Make avec Chocolatey :
     ```bash
     choco install make
     ```
   - Sinon, utilisez **Git Bash**, **WSL**, ou un autre environnement UNIX-like.

---

## Installation

### Cloner le projet
Exécutez les commandes suivantes dans votre terminal :
```bash
git clone https://github.com/votre-utilisateur/projet-IN-510.git
cd projet-IN-510
```

---

## Comment exécuter

### Avec Make

#### Exécuter les scripts
Pour exécuter tous les scripts, utilisez la commande suivante :
```bash
make
```

