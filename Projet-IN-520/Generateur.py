import sys
import re

class Generateur:
    def __init__(self, fichier, longueur_max):
        self.regles = {}
        self.axiome = None
        self.longueur_max = longueur_max
        self.lire_grammaire(fichier)

    def lire_grammaire(self, fichier):
        """Lit la grammaire à partir d'un fichier."""
        with open(fichier, "r") as f:
            for ligne in f:
                ligne = ligne.strip()
                if "->" in ligne:
                    gauche, droite = ligne.split("->")
                    gauche = gauche.strip()
                    sequences = [seq.strip() for seq in droite.split("|")]
                    if self.axiome is None:
                        self.axiome = gauche
                    self.regles[gauche] = sequences
        #print(f"Grammaire chargée : {self.regles}")  # Affiche la grammaire pour vérifier

    def analyser_sequence(self, sequence):
        """
        Analyse une séquence pour séparer les symboles non-terminaux (majuscules) 
        des terminaux (minuscules ou chaînes définies dans les règles).
        """
        pattern = re.compile(r'(?:[A-Z]\d*|E|[a-z])')
        return pattern.findall(sequence)

    def generer_mots(self):
        """Génère tous les mots de longueur inférieure ou égale à longueur_max."""
        mots = set()
        pile = [[self.axiome]]  # Démarre avec l'axiome sous forme de liste contenant des symboles séparés
        visites = set()  # Ensemble des séquences déjà développées

        while pile:
            courant = pile.pop()
            courant_tuple = tuple(courant)
            if courant_tuple in visites:
                continue
            visites.add(courant_tuple)

            #print(f"Développement : {courant}")  # Affiche l'état actuel de la chaîne en développement

            # Ajouter au résultat si terminal et longueur valide
            mot_actuel = "".join(courant)
            if len(mot_actuel) <= self.longueur_max + 1 and all(
                symbole not in self.regles for symbole in courant
            ):
                mot_sans_e = "".join(symb for symb in courant if symb != "E")

                if len(mot_sans_e) <= self.longueur_max and all(
                    # On s'assure que le symbole n'est pas un non-terminal
                    # (i.e. n’apparaît pas comme clé de self.regles)
                    symbole not in self.regles
                    for symbole in courant
                    if symbole != "E"
                ):
                    mots.add(mot_sans_e)
                    #print(f"Mot valide ajouté : {mot_sans_e}")
                    continue
                
            # Si la longueur dépasse, on ne développe pas
            if len(mot_actuel) > self.longueur_max + 2:
                #print(f"Longueur dépassée, chaîne ignorée : {mot_actuel}")  # Affiche si la chaîne dépasse la longueur max
                continue

            # Remplacer le premier non-terminal trouvé
            for i, symbole in enumerate(courant):
                if symbole in self.regles:  # Si c'est un non-terminal
                    #print(f"Développement de {symbole} à l'index {i}")  # Affiche quel non-terminal est développé
                    for expansion in self.regles[symbole]:
                        # Analyser la séquence pour séparer les terminaux et non-terminaux
                        nouvelle_sequence = courant[:i] + self.analyser_sequence(expansion) + courant[i + 1:]
                        #print(f"Nouvelle séquence générée : {''.join(nouvelle_sequence)}")  # Affiche la nouvelle séquence
                        pile.append(nouvelle_sequence)
                    break  # Un seul non-terminal est développé à la fois
        return sorted(mots)  # Tri lexicographique des mots

    def afficher_mots(self, mots):
        """Affiche les mots un par ligne."""
        for mot in mots:
            print(mot)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        #print("python Generateur.py <longueur_max> <fichier_grammaire>")
        sys.exit(1)

    longueur_max = int(sys.argv[1])
    fichier_grammaire = sys.argv[2]

    generateur = Generateur(fichier_grammaire, longueur_max)
    mots = generateur.generer_mots()
    generateur.afficher_mots(mots)
