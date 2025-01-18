import sys
import re
from collections import deque

class Generateur:
    def __init__(self, fichier, longueur_max):
        self.regles = {}
        self.axiome = None
        self.longueur_max = longueur_max
        self.lire_grammaire(fichier)

    def lire_grammaire(self, fichier):
        """Lit la grammaire à partir d'un fichier, où chaque ligne a la forme :
             NonTerminal : Production1 | Production2 | ...
        Exemple:
            S0 : aS0b | E
        """
        with open(fichier, "r") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue  # ignore les lignes vides
                if ":" in ligne:
                    gauche, droite = ligne.split(":")
                    gauche = gauche.strip()
                    # On sépare les alternatives par '|'
                    sequences = [seq.strip() for seq in droite.split("|")]
                    if self.axiome is None:
                        self.axiome = gauche
                    self.regles[gauche] = sequences

    def analyser_sequence(self, sequence):
        """
        Sépare les symboles non-terminaux (majuscules + chiffres)
        des terminaux (minuscules) et 'E' (epsilon).
        Exemple : "A0a" => ["A0", "a"], "E" => ["E"].

        Si la grammaire peut générer des choses non conformes,
        la regex peut laisser de côté certains caractères (dans ce cas, on vérifie).
        """
        pattern = re.compile(r'[a-z]|[A-Z]\d*|E')
        tokens = pattern.findall(sequence)

        # Si vous voulez déboguer les symboles non reconnus :
        # re_check = pattern.sub('', sequence)
        # if re_check:
        #     print("Attention, certains caractères n'ont pas été captés :", re_check)

        return tokens

    def generer_mots(self):
        """
        Génère tous les mots de longueur (en terminaux) <= self.longueur_max,
        en tenant compte que 'E' correspond à epsilon.
        """
        mots = set()
        file = deque()
        file.append([self.axiome])
        deja_vu = set()
        deja_vu.add(tuple([self.axiome]))

        while file:
            courant = file.popleft()

            # Compte le nb de terminaux réels (hors 'E')
            nb_terminaux = sum(
                1 for symb in courant
                if symb not in self.regles and symb != 'E' and symb is not None
            )
            if nb_terminaux > self.longueur_max:
                # Trop de terminaux => on coupe
                continue

            # On ajoute une limite de taille totale pour éviter l'explosion
            if len(courant) > 2 * self.longueur_max:
                continue

            # Vérifie si c'est entièrement terminal (ou 'E'/None)
            # => aucun symbole n'est dans self.regles
            est_entierement_terminal = all(
                (symb not in self.regles) for symb in courant if symb is not None
            )

            if est_entierement_terminal:
                # Convertit en mot (supprime 'E' et None)
                mot = "".join(
                    s for s in courant
                    if (s is not None) and (s != 'E')
                )
                if len(mot) <= self.longueur_max:
                    mots.add(mot)
                # Pas besoin de développer plus loin cette séquence
                continue

            # Sinon, on remplace le premier non-terminal
            for i, symbole in enumerate(courant):
                if symbole is not None and symbole in self.regles:
                    # Pour chaque expansion possible
                    for expansion_str in self.regles[symbole]:
                        tokens = self.analyser_sequence(expansion_str)
                        nouvelle = courant[:i] + tokens + courant[i+1:]
                        t_nouvelle = tuple(nouvelle)
                        if t_nouvelle not in deja_vu:
                            deja_vu.add(t_nouvelle)
                            file.append(nouvelle)
                    break  # on remplace un seul NT à la fois

        return sorted(mots)

    def afficher_mots(self, mots):
        """Affiche les mots un par ligne."""
        for mot in mots:
            print(mot)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python Generer.py <longueur_max> <fichier_grammaire>")
        sys.exit(1)

    longueur_max = int(sys.argv[1])
    fichier_grammaire = sys.argv[2]

    generateur = Generateur(fichier_grammaire, longueur_max)
    mots = generateur.generer_mots()
    generateur.afficher_mots(mots)