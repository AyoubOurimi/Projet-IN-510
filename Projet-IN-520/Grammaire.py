import sys
from collections import defaultdict

##############################
# Générateur de non-terminaux
##############################
class GenerateurNonTerminaux:
    """Création de non-terminaux (A0, A1, ... Z9 (en évitant E))."""
    def __init__(self):
        self.lettres = [chr(c) for c in range(ord('A'), ord('Z')+1) if chr(c) != 'E']
        self.index = 0

    def suivant(self):
        if self.index >= 250:
            raise ValueError("Trop de non-terminaux utilisés ! (max 250)")
        lettre = self.lettres[self.index // 10]
        digit = self.index % 10
        self.index += 1
        return f"{lettre}{digit}"

##############################
# Classe Grammaire
##############################
class Grammaire:
    def __init__(self):
        self.regles = defaultdict(list)
        self.axiome = None
        self.genNT = GenerateurNonTerminaux()

    ##############################
    # Lecture / écriture
    ##############################
    def lire(self, fichier):
        """Lecture du fichier .general en entrée
        Fichier du genre :
            S -> AB | a
            A -> aA | E"""
        with open(fichier, "r") as f:
            for ligne in f:
                ligne = ligne.strip().replace(" ", "")
                if ligne:
                    gauche, droite = ligne.split("->")
                    if self.axiome is None:
                        self.axiome = gauche
                    for seq in droite.split("|"):
                        self.regles[gauche].append(list(seq))

    def ecrire(self, fichier):
        """Renvoit la grammaire dans un fichier. Les epsilon sont notées "E"."""
        with open(fichier, "w") as f:
            for gauche, list_seq in self.regles.items():
                droites = []
                for seq in list_seq:
                    if seq == []:
                        droites.append("E")
                    else:
                        droites.append("".join(seq))
                line = " | ".join(droites)
                f.write(f"{gauche} -> {line}\n")

    def afficher_regles(self, message):
        """Affiche la grammaire à l'écran. (FONCTION DE DEBUG)"""
        for gauche, list_seq in self.regles.items():
            if list_seq:
                droites = []
                for seq in list_seq:
                    if seq == []:
                        droites.append("E")
                    else:
                        droites.append("".join(seq))
                #print(f"{gauche} -> {' | '.join(droites)}")


    ##############################
    # Méthodes Chomsky
    ##############################
    def chomsky(self):
        """
        Transformation en forme normale de Chomsky.
          - reduire (supprime symboles inutiles)
          - _start
          - _term
          - _bin
          - _del_epsilon
          - _unit
          - _nettoyer_regles
        """
        self.afficher_regles("Avant réduction :")
        self.reduire()
        self.afficher_regles("Après réduction :")
        self._start()
        self.afficher_regles("Après START :")
        self._term()
        self.afficher_regles("Après TERM :")
        self._bin()
        self.afficher_regles("Après BIN :")
        self._del_epsilon()
        self.afficher_regles("Après DEL :")
        self._unit()
        self.afficher_regles("Après UNIT :")
        self._nettoyer_regles()
        self.afficher_regles("Après nettoyage :")
        return self.regles

    ##############################
    # Méthodes Greibach
    ##############################
    def greibach(self):
        """
        Transformation en forme normale de Greibach:
          1) Lister les non-terminaux dans un certain ordre (axiome en premier).
          2) Pour i=1..n:
               - pour j=1..i-1: substituer A_j dans A_i
               - éliminer récursivité gauche directe sur A_i
          3) Placer un terminal en tête
          4) _del_epsilon
          5) Validation forme normale de Greibach
        """
        self.afficher_regles("Avant transformation Greibach :")

        #1) On liste les NT dans un ordre
        non_terminaux = list(self.regles.keys())
        if self.axiome in non_terminaux:
            non_terminaux.remove(self.axiome)
            non_terminaux.insert(0, self.axiome)

        #2) Substitutions + élimination recursion gauche
        for i in range(len(non_terminaux)):
            Ai = non_terminaux[i]
            if Ai not in self.regles:
                continue

            # pour j < i, on substitue
            for j in range(i):
                Aj = non_terminaux[j]
                if Aj not in self.regles:
                    continue
                self._substitution(Ai, Aj)

            # éliminer rec. gauche directe
            self._elim_recursivite_gauche_directe(Ai)
        self.afficher_regles("Après Substitutions + récursion gauche :")
        # On créer ou non un S0
        self._start_greibach()
        self.afficher_regles("Après START :")

        # 3) Placer un terminal en tête
        self._placer_terminal_en_tete()
        self.afficher_regles("Après terminaux en tête :")

        # 4) suppression des epsilon en dehors de l'axiome:
        self._del_epsilon()
        self.afficher_regles("Après DEL \n Forme finale :")
        self._valider_greibach()

    ##############################
    # Sous-fonctions communes
    ##############################
    def reduire(self):
        """Supprime symboles non-accessibles + non-coaccessibles."""
        coaccessibles = self._trouver_coaccessibles()
        accessibles = self._trouver_accessibles()
        self._filtrer_regles(accessibles)

    def _start(self):
        """Ajoute un nouvel axiome S0 -> S."""
        nouvel_axiome = "S0"
        if nouvel_axiome not in self.regles:
            self.regles[nouvel_axiome] = []
        self.regles[nouvel_axiome].append([self.axiome])
        self.axiome = nouvel_axiome

    def _term(self):
        """Remplace les terminaux par des non-terminaux (sauf si la règle = 1 terminal)."""
        nouvelles_regles = {}
        for gauche, sequences in self.regles.items():
            for seq in sequences:
                for i, symbole in enumerate(seq):
                    # Si c'est un terminal (miniscule avec islower) et qu'il n'est pas seul
                    if symbole.islower() and (i > 0 or len(seq) > 1):
                        nouveau = self.genNT.suivant()
                        if nouveau not in nouvelles_regles:
                            nouvelles_regles[nouveau] = [[symbole]]
                        seq[i] = nouveau
        # on fusionne
        for k, v in nouvelles_regles.items():
            self.regles[k] = v

    def _bin(self):
        """transformer règles de longueur > 2."""
        nouvelles_regles = {}
        for gauche, sequences in self.regles.items():
            for seq in sequences:
                while len(seq) > 2:
                    nouveau = self.genNT.suivant()
                    nouvelles_regles[nouveau] = [seq[1:]]
                    seq[:] = [seq[0], nouveau]
        for k, v in nouvelles_regles.items():
            self.regles[k] = v

    def _del_epsilon(self):
        """Supprimer les epsilon-règles hors axiome."""
        annulables = self._trouver_annulables()
        nouvelles_regles = defaultdict(list)
        for gauche, sequences in self.regles.items():
            for seq in sequences:
                if seq == ["E"] and gauche == self.axiome:
                    # on conserve si c'est l'axiome
                    nouvelles_regles[gauche].append(["E"])
                elif seq != ["E"]:
                    combos = self._generer_combinaisons(seq, annulables)
                    for c in combos:
                        if c == [] and gauche != self.axiome:
                            # ignore epsilon hors axiome
                            continue
                        nouvelles_regles[gauche].append(c)
        self.regles = nouvelles_regles

    def _generer_combinaisons(self, seq, annulables):
        """Génère toutes combinaisons en retirant les symboles annulables."""
        combi = {tuple(seq)}
        for i, s in enumerate(seq):
            if s in annulables:
                new_combi = set()
                for c in combi:
                    # suppr le s i
                    c_list = list(c)
                    del c_list[i]
                    new_combi.add(tuple(c_list))
                combi |= new_combi
        return list(map(list, combi))

    def _unit(self):
        """Supprime les règles unitaires (A->B)."""
        for gauche, list_seq in list(self.regles.items()):
            nouvelles = []
            for seq in list_seq:
                if len(seq) == 1 and seq[0].isupper():
                    # On remplace par les alternatives de seq[0]
                    nouvelles.extend(self.regles[seq[0]])
                else:
                    nouvelles.append(seq)
            self.regles[gauche] = nouvelles

    def _nettoyer_regles(self):
        """Supprime doublons etc."""
        for gauche, list_seq in self.regles.items():
            uniques = []
            for seq in list_seq:
                if seq not in uniques:
                    uniques.append(seq)
            self.regles[gauche] = uniques


    ##############################
    # Sous-fonctions Greibach
    ##############################
    def _start_greibach(self):
        """
        Crée un nouvel axiome S0 uniquement si:
        - La grammaire peut produire le mot vide (il existe un X -> E), ET
        - L'axiome actuel n'est pas annulable.
        Sinon on ne fait rien du tout
        """
        # on vérif si il y a au moins un E dans notre grammaire
        grammaire_a_epsilon = any(any(seq == ["E"] for seq in seqs)for seqs in self.regles.values())
        if not grammaire_a_epsilon:
            # => pas besoin de S0 car pas de epsilon
            return

        #on vérif si l'axiome est annulable
        annulables = self._trouver_annulables()
        if self.axiome in annulables:
            #l'axiome peut déjà faire E on return
            return

        #sinon on créer un axiome S0 -> S | E
        nouvel_axiome = "S0"
        if nouvel_axiome not in self.regles:
            self.regles[nouvel_axiome] = []
        # règle S0 -> S
        self.regles[nouvel_axiome].append([self.axiome])
        # règle S0 -> E
        self.regles[nouvel_axiome].append(["E"])
        self.axiome = nouvel_axiome

    def _substitution(self, Ai, Aj):
        """
        Substitue dans Ai les règles Ai->Aj alpha
        en Ai->(prodAj) alpha, pour chaque prodAj de Aj.
        """
        nouvelles = []
        for seq in self.regles[Ai]:
            if seq and seq[0] == Aj:
                suffix = seq[1:]
                for alt in self.regles[Aj]:
                    nouvelles.append(alt + suffix)
            else:
                nouvelles.append(seq)
        self.regles[Ai] = nouvelles

    def _elim_recursivite_gauche_directe(self, Ai):
        """
        A_i -> A_i X => on élimine la rec gauche
        On crée un Ai' si besoin
        """
        alpha = []
        beta = []
        for seq in self.regles[Ai]:
            if seq and seq[0] == Ai:
                # recur gauche
                alpha.append(seq[1:])
            else:
                beta.append(seq)
        if not alpha:
            return

        Ai_prime = self.genNT.suivant()
        self.regles[Ai_prime] = []

        # A_i -> beta Ai'
        new_Ai = []
        for b in beta:
            new_Ai.append(b + [Ai_prime])
        self.regles[Ai] = new_Ai

        # Ai' -> alpha Ai' | E
        new_Ai_prime = []
        for a in alpha:
            new_Ai_prime.append(a + [Ai_prime])
        new_Ai_prime.append(["E"])
        self.regles[Ai_prime] = new_Ai_prime

    def _placer_terminal_en_tete(self):
        """
        Tant qu'une règle commence par un non-terminal X,
        on substitue X par ses alternatives.
        """
        changed = True
        while changed:
            changed = False
            for nt, list_seq in list(self.regles.items()):
                nouvelles = []
                for seq in list_seq:
                    if seq == []:
                        # epsilon
                        nouvelles.append(seq)
                    elif seq[0].islower():
                        # déjà terminal
                        nouvelles.append(seq)
                    else:
                        head = seq[0]
                        if head in self.regles:
                            # substituer
                            for alt in self.regles[head]:
                                nouvelles.append(alt + seq[1:])
                            changed = True
                        else:
                            # inconnu ? on laisse
                            nouvelles.append(seq)
                self.regles[nt] = nouvelles

    def _valider_greibach(self):
        for gauche, list_seq in self.regles.items():
            for seq in list_seq:
                if seq == []:
                    # epsilon => autorisé si c'est l'axiome
                    if gauche != self.axiome:
                        raise ValueError(f"Règle {gauche} -> ε hors axiome interdit")
                elif seq == ["E"]:
                    # on autorise seulement si c'est l'axiome
                    if gauche != self.axiome:
                        raise ValueError(f"Règle {gauche} -> E hors axiome interdit")
                else:
                    # Règle "normale" => doit commencer par un minuscule
                    if not seq[0].islower():
                        raise ValueError(
                            f"La règle {gauche} -> {''.join(seq)} "
                            "ne commence pas par un terminal => pas forme normale de greibach"
                        )

    ##############################
    # Fonctions d'accessibilité
    ##############################
    def _trouver_annulables(self):
        annulables = set()
        for g, seqs in self.regles.items():
            for s in seqs:
                if s == ["E"] or s == []:
                    annulables.add(g)
        return annulables

    def _trouver_coaccessibles(self):
        coaccessibles = set()
        changement = True
        while changement:
            changement = False
            for g, seqs in self.regles.items():
                if g in coaccessibles:
                    continue
                for s in seqs:
                    if all(symb.islower() or symb in coaccessibles for symb in s if symb != "E"):
                        coaccessibles.add(g)
                        changement = True
                        break
        #print("Variables coaccessibles :", coaccessibles)
        return coaccessibles

    def _trouver_accessibles(self):
        accessibles = {self.axiome}
        changement = True
        while changement:
            changement = False
            for g, seqs in self.regles.items():
                if g in accessibles:
                    for s in seqs:
                        for symb in s:
                            if symb.isupper() and symb not in accessibles:
                                accessibles.add(symb)
                                changement = True
        #print("Variables accessibles :", accessibles)
        return accessibles

    def _filtrer_regles(self, accessibles):
        new_regles = {}
        for g, seqs in self.regles.items():
            if g in accessibles:
                newseqs = []
                for s in seqs:
                    # on garde la prod si tous ses symboles NT sont dans accessibles
                    if all((not x.isupper()) or (x in accessibles) for x in s):
                        newseqs.append(s)
                if newseqs:
                    new_regles[g] = newseqs
        self.regles = new_regles
        #print("Règles après accessibilité :", self.regles)

##############################
# MAIN
##############################
if __name__ == "__main__":
    if len(sys.argv) < 2:
        #print("python grammaire.py <fichier.general>")
        sys.exit(1)

    fichier_entree = sys.argv[1]
    fichier_sortie_chom = fichier_entree.replace(".general", ".chomsky")
    fichier_sortie_grei = fichier_entree.replace(".general", ".greibach")

    # Partie Chomsky
    g_chomsky = Grammaire()
    g_chomsky.lire(fichier_entree)
    g_chomsky.chomsky()
    g_chomsky.ecrire(fichier_sortie_chom)
    #print(f"forme normale de Chomsky dans {fichier_sortie_chom}.")

    # Partie Greibach
    g_greibach = Grammaire()
    g_greibach.lire(fichier_entree)
    g_greibach.greibach()
    g_greibach.ecrire(fichier_sortie_grei)
    #print(f"forme normale de Greibach dans {fichier_sortie_grei}")