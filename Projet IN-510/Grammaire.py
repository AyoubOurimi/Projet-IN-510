#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from collections import defaultdict, deque

########################################
#  REGEX pour séparer terminaux et NT
########################################
# Un terminal = une lettre minuscule
# Un non-terminal = 1 lettre majuscule + 0..n chiffres
REGEX_SYMBOLE = re.compile(r"[a-z]|[A-Z]\d*")

def is_epsilon(seq):
    """Vrai si la séquence représente ε (liste vide)."""
    return (len(seq) == 0)

########################################
# Générateur de variables (non-terminaux)
########################################
class GenerateurNonTerminaux:
    """Crée des noms de variables (A0, A1, ..., Z9) en évitant 'E', 
       et surtout en évitant ceux déjà dans la grammaire."""
    def __init__(self, already_used=None):
        # on exclut la lettre 'E' pour ne pas confondre avec epsilon
        self.lettres = [chr(c) for c in range(ord('A'), ord('Z')+1) if chr(c) != 'E']
        self.index = 0
        if already_used is None:
            already_used = set()
        self.already_used = set(already_used)

    def suivant(self):
        """Génère la prochaine variable qui n'appartient pas déjà à self.already_used."""
        while True:
            if self.index >= 250:
                raise ValueError("Trop de non-terminaux !")
            lettre = self.lettres[self.index // 10]
            digit = self.index % 10
            candidate = f"{lettre}{digit}"
            self.index += 1
            if candidate not in self.already_used:
                self.already_used.add(candidate)
                return candidate

########################################
# Classe Grammaire
########################################
class Grammaire:
    """
    Une grammaire stockée comme un dictionnaire { NT : [liste_de_sequences] }.
    Chaque séquence est une liste de symboles (NT ou terminaux).
    Epsilon est représenté comme la liste vide [] en interne.
    """
    def __init__(self):
        self.regles = defaultdict(list)
        self.axiome = None
        self.genNT = None

    def lire(self, fichier):
        """
        Lecture d'un fichier .general :
          S0 -> aS0b | E
          ...
        On convertit 'E' en la liste vide [], et on segmente 'aS0b' => ['a','S0','b'] grâce à la regex.
        """
        with open(fichier, "r") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue  # ligne vide
                # retirer les espaces
                ligne_sans_espace = ligne.replace(" ", "")

                # séparation de la gauche et la droite
                gauche, droite = ligne_sans_espace.split(":")

                # le premier non-terminal lu devient l'axiome si self.axiome n'est pas encore défini
                if self.axiome is None:
                    self.axiome = gauche

                # on sépare les alternatives par '|'
                for prod_str in droite.split("|"):
                    if prod_str == "E":  # epsilon
                        self.regles[gauche].append([])
                    else:
                        # on repere les non terminaux et les terminaux
                        tokens = REGEX_SYMBOLE.findall(prod_str)
                        self.regles[gauche].append(tokens)

        # maintenant qu'on a lu toutes les règles, on recense les noms déjà utilisés
        used_nts = set(self.regles.keys())  # NT utilisés en tête de règles
        # on ajoute aussi tous les symboles majuscules qu'on trouve à droite
        for prod_list in self.regles.values():
            for seq in prod_list:
                for symb in seq:
                    if symb.isupper():
                        used_nts.add(symb)

        # on initialise le générateur de noms avec les NT déjà existants
        self.genNT = GenerateurNonTerminaux(already_used=used_nts)

    def ecrire(self, fichier):
        """
        Écrit la grammaire dans un fichier, en recollant les symboles, et en
        remplaçant [] par 'E' pour l'epsilon.
        """
        with open(fichier, "w") as f:
            # forcer l'écriture du nouvel axiome en premier
            cles = [self.axiome] + [nt for nt in self.regles if nt != self.axiome]
            deja_vu = set()
            for gauche in cles:
                if gauche not in self.regles:
                    continue
                if gauche in deja_vu:
                    continue
                deja_vu.add(gauche)

                prod_list = self.regles[gauche]
                droites = []
                for seq in prod_list:
                    if is_epsilon(seq):
                        droites.append("E")
                    else:
                        droites.append("".join(seq))
                line = " | ".join(droites)
                f.write(f"{gauche} : {line}\n")

    def afficher_regles(self, message=""):
        """Debug : affiche la grammaire."""
        #print(f"\n--- {message} ---")
        for gauche, seqs in self.regles.items():
            droites = []
            for seq in seqs:
                droites.append("E" if is_epsilon(seq) else "".join(seq))
            #print(f"{gauche} -> {' | '.join(droites)}")

    #############################
    # 0) Réduction (symboles utiles)
    #############################
    def reduire(self):
        """Supprime les symboles non utiles : inaccessibles ou non coaccessibles."""
        # on calcule l'intersection des variables accessibles et coaccessibles
        accessibles = self._trouver_accessibles()
        coaccessibles = self._trouver_coaccessibles()
        utilises = accessibles.intersection(coaccessibles)
        self._filtrer_regles(utilises)

    def _trouver_accessibles(self):
        """Non-terminaux accessibles depuis l'axiome."""
        acces = set()
        if self.axiome:
            acces = {self.axiome}
        changed = True
        while changed:
            changed = False
            for A, prod_list in self.regles.items():
                if A in acces:
                    for seq in prod_list:
                        for symb in seq:
                            if symb.isupper() and symb not in acces:
                                acces.add(symb)
                                changed = True
        return acces

    def _trouver_coaccessibles(self):
        """
        Non-terminaux coaccessibles = ceux qui peuvent produire un mot de terminaux.
        On tient compte de l'epsilon et on itère jusqu'à fixpoint.
        """
        annulables = self._trouver_annulables()
        coacc = set()
        changed = True
        while changed:
            changed = False
            for A, prod_list in self.regles.items():
                if A in coacc:
                    continue
                # si A -> seq entièrement réductible en terminaux => A coaccessible
                for seq in prod_list:
                    if self._seq_coaccessible(seq, coacc, annulables):
                        coacc.add(A)
                        changed = True
                        break
        return coacc

    def _seq_coaccessible(self, seq, coacc, annulables):
        """
        Vérifie si la séquence 'seq' peut être réduite entièrement en terminaux,
        en considérant :
         - un terminal (minuscule) est déjà terminal
         - un NT dans coacc => on peut le remplacer par des terminaux
         - un NT dans annulables => on peut l'effacer
        """
        for symb in seq:
            if symb.islower():
                # OK c'est un terminal
                continue
            elif symb in annulables:
                # on peut l'ignorer
                continue
            else:
                # c'est un non-terminal non annulable => il faut qu'il soit coaccessible
                if symb not in coacc:
                    return False
        return True

    def _filtrer_regles(self, nts_a_garder):
        """Ne conserve que les règles dont la partie gauche est dans nts_a_garder
           et dont tous les NT à droite sont aussi dans nts_a_garder."""
        new_regles = {}
        for A, prod_list in self.regles.items():
            if A in nts_a_garder:
                filtered = []
                for seq in prod_list:
                    # on garde si tous les NT sont dans nts_a_garder
                    if all(not x.isupper() or x in nts_a_garder for x in seq):
                        filtered.append(seq)
                if filtered:
                    new_regles[A] = filtered
        self.regles = new_regles

    #############################
    # Méthodes Chomsky
    #############################
    def chomsky(self):
        """
        Suit l'ordre standard : REDUCTION -> START -> TERM -> BIN -> DEL -> UNIT
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

        # nettoyer d'éventuels doublons
        self._nettoyer_regles()
        # >>>>>> CHANGEMENT ICI <<<<<<
        self.afficher_regles("Après nettoyage :")  
        

    #############################
    # (CHOMSKY) START
    #############################
    def _start(self):
        """
        START : introduit un nouvel axiome S0 -> S si l'axiome S est différent de 'S0'.
        """
        if self.axiome and self.axiome != "S0":
            S0 = "S0"
            # S'il n'existe pas encore de règle pour S0, on l'initialise
            if S0 not in self.regles:
                self.regles[S0] = []
            # On ajoute la règle S0 -> (ancien axiome)
            self.regles[S0].append([self.axiome])
            self.axiome = S0

    #############################
    # (CHOMSKY) TERM
    #############################
    def _term(self):
        """
        TERM : Si un terminal apparaît dans une règle de longueur >= 2,
        on le remplace par un nouveau NT, et on crée la règle correspondante.
        """
        nouvelles_regles = {}
        for A, prod_list in self.regles.items():
            for seq in prod_list:
                if len(seq) < 2:
                    continue
                for i, symb in enumerate(seq):
                    if symb.islower():
                        # cherche si on a déjà un NT pour ce terminal
                        nt_equiv = None
                        for x, rhs in nouvelles_regles.items():
                            # rhs == [[symb]] => la règle x->symb
                            if len(rhs) == 1 and rhs[0] == [symb]:
                                nt_equiv = x
                                break
                        if not nt_equiv:
                            # on en crée un
                            nt_equiv = self.genNT.suivant()
                            nouvelles_regles[nt_equiv] = [[symb]]
                        seq[i] = nt_equiv

        # fusion
        for nt, rhs in nouvelles_regles.items():
            if nt not in self.regles:
                self.regles[nt] = rhs

    #############################
    # (CHOMSKY) BIN
    #############################
    def _bin(self):
        """
        BIN : On remplace les règles de longueur > 2 par des règles binaires
        du style X -> Y Z, en introduisant des variables intermédiaires.
        """
        to_add = {}
        for A, prod_list in self.regles.items():
            new_list = []
            for seq in prod_list:
                # tant que la longueur > 2, on réduit
                while len(seq) > 2:
                    X = seq[0]
                    Y = seq[1]
                    reste = seq[2:]
                    new_nt = self.genNT.suivant()
                    to_add.setdefault(new_nt, []).append([Y] + reste)
                    seq = [X, new_nt]
                new_list.append(seq)
            self.regles[A] = new_list

        for nt, rhs in to_add.items():
            if nt not in self.regles:
                self.regles[nt] = rhs
            else:
                self.regles[nt].extend(rhs)

    #############################
    # (CHOMSKY) DEL
    #############################
    def _del_epsilon(self):
        """
        DEL : supprime les ε-règles (sauf éventuellement celle de l'axiome).
        """
        annulables = self._trouver_annulables()
        new_reg = defaultdict(list)

        for A, prod_list in self.regles.items():
            for seq in prod_list:
                if is_epsilon(seq):
                    # si c'est l'axiome, on le garde, sinon on ignore
                    if A == self.axiome:
                        new_reg[A].append([])
                else:
                    combos = self._generer_combinaisons(seq, annulables)
                    for c in combos:
                        if len(c) == 0 and A != self.axiome:
                            continue
                        if c not in new_reg[A]:
                            new_reg[A].append(c)
        self.regles = new_reg

    def _trouver_annulables(self):
        """Renvoie l'ensemble des NT qui peuvent produire epsilon."""
        annulables = set()
        changed = True
        while changed:
            changed = False
            for A, prods in self.regles.items():
                if A not in annulables:
                    for seq in prods:
                        if is_epsilon(seq) or all(x in annulables for x in seq):
                            annulables.add(A)
                            changed = True
                            break
        return annulables

    def _generer_combinaisons(self, seq, annulables):
        """
        Génère toutes les combinaisons en retirant zéro ou plusieurs
        symboles annulables.
        """
        combi = {tuple(seq)}
        changed = True
        while changed:
            changed = False
            new_combi = set(combi)
            for c in combi:
                c_list = list(c)
                for i, s in enumerate(c_list):
                    if s in annulables:
                        c_copy = c_list[:i] + c_list[i+1:]
                        new_combi.add(tuple(c_copy))
            if len(new_combi) > len(combi):
                combi = new_combi
                changed = True
        return list(map(list, combi))

    #############################
    # (CHOMSKY) UNIT
    #############################
    def _unit(self):
        """
        UNIT : supprime toutes les règles unitaires A->B en une seule passe,
        via la fermeture transitive (sans boucle infinie).
        """
        adjacency = defaultdict(list)
        # construire le graphe unitaire
        for A, productions in self.regles.items():
            for p in productions:
                if len(p) == 1 and p[0].isupper() and p[0] != A:
                    adjacency[A].append(p[0])

        closure = {A: {A} for A in self.regles}
        for A in self.regles:
            queue = deque(adjacency[A])
            while queue:
                B = queue.popleft()
                if B not in closure[A]:
                    closure[A].add(B)
                    for C in adjacency[B]:
                        if C not in closure[A]:
                            queue.append(C)

        new_reg = defaultdict(list)
        for A in self.regles:
            # on recopie les règles NON-unitaires de A
            for p in self.regles[A]:
                if not (len(p) == 1 and p[0].isupper()):
                    if p not in new_reg[A]:
                        new_reg[A].append(p)
            # on ajoute les règles non-unitaires de tous B in closure[A]
            for B in closure[A]:
                if B == A:
                    continue
                for pB in self.regles[B]:
                    if not (len(pB) == 1 and pB[0].isupper()):
                        if pB not in new_reg[A]:
                            new_reg[A].append(pB)
        self.regles = new_reg

    #############################
    # Nettoyage
    #############################
    def _nettoyer_regles(self):
        """Supprime les doublons éventuels."""
        for A, seqs in self.regles.items():
            uniques = []
            for s in seqs:
                if s not in uniques:
                    uniques.append(s)
            self.regles[A] = uniques

    #############################
    # Méthodes Greibach
    #############################
    def greibach(self):
        """
        Forme normale de Greibach, en suivant Wikipédia :
          1) Suppression des ε-règles (hors axiome).
          2) Suppression des règles unité.
          3) Mise en Forme normale de Greibach (on numérote A1..An, on élim. la récursivité gauche, etc.)
          4) Pour éviter l'erreur "ne commence pas par un terminal", on fait une passe finale
             de substitution si un NT apparaît en tête.
        """
        self.afficher_regles("Avant transformation Greibach :")

        # 1) DEL (epsilon) hors axiome
        self._del_epsilon_greibach()
        self.afficher_regles("Après suppression epsilon :")

        # 2) UNIT
        self._unit()
        self.afficher_regles("Après suppression des règles unité :")

        # 3) mise sous forme Greibach
        self._mise_sous_forme_greibach()
        # 4) dernière passe pour substituer les non-terminaux en tête

        self._final_placer_terminal_en_tete()

        self.afficher_regles("Après mise en forme Greibach :")

        # on valide
        self._valider_greibach()

    def _del_epsilon_greibach(self):
        """
        Suppression epsilon en phase préliminaire Greibach.
        On autorise Axiome->ε si besoin.
        """
        annulables = self._trouver_annulables()
        new_reg = defaultdict(list)

        for A, prod_list in self.regles.items():
            for seq in prod_list:
                if is_epsilon(seq):
                    if A == self.axiome:
                        new_reg[A].append([])
                else:
                    combos = self._generer_combinaisons(seq, annulables)
                    for c in combos:
                        if len(c) == 0 and A != self.axiome:
                            continue
                        if c not in new_reg[A]:
                            new_reg[A].append(c)
        self.regles = new_reg

    def _mise_sous_forme_greibach(self):
        """
        On suppose la grammaire sans ε-règles (hors axiome) et sans règles unité.
        On numérote les variables (l'ordre : axiome d'abord, puis les autres).
        Ensuite, pour i=1..n:
          - Pour j < i : substituer A_j s'il apparaît en tête
          - Éliminer la récursivité gauche directe
        Puis on remplace les terminaux au milieu par des NT (petit TERM).
        """
        # 1) récupère la liste de tous les non-terminaux
        nts = list(self.regles.keys())
        # 2) on met l'axiome en premier
        if self.axiome in nts:
            nts.remove(self.axiome)
            nts.insert(0, self.axiome)

        # 3) on applique la méthode pour tout
        for i in range(len(nts)):
            Ai = nts[i]
            if Ai not in self.regles:
                continue
            # substitutions : pour j < i
            for j in range(i):
                Aj = nts[j]
                if Aj not in self.regles:
                    continue
                self._substitution_greibach(Ai, Aj)
            # elim. récursion gauche
            self._elim_recursivite_gauche_directe(Ai)

        # on remplace les terminaux au milieu
        self._term_greibach()

    def _substitution_greibach(self, Ai, Aj):
        """
        Dans Ai-> Aj alpha, on remplace par les productions de Aj concaténées à alpha.
        """
        new_list = []
        for seq in self.regles[Ai]:
            if seq and seq[0] == Aj:
                suffix = seq[1:]
                for alt in self.regles[Aj]:
                    new_list.append(alt + suffix)
            else:
                new_list.append(seq)
        self.regles[Ai] = new_list

    def _elim_recursivite_gauche_directe(self, Ai):
        """
        Élimine la récursivité gauche : Ai->Ai alpha | ... => on crée Ai'
        """
        alpha = []
        beta = []
        for seq in self.regles[Ai]:
            if seq and seq[0] == Ai:
                alpha.append(seq[1:])
            else:
                beta.append(seq)
        if not alpha:
            return

        # crée Ai'
        Aiprime = self.genNT.suivant()
        self.regles[Aiprime] = []

        # Ai-> beta Ai'
        newAi = []
        for b in beta:
            newAi.append(b + [Aiprime])
        self.regles[Ai] = newAi

        # Ai'-> alpha Ai' | epsilon
        newAiPrime = []
        for a in alpha:
            newAiPrime.append(a + [Aiprime])
        newAiPrime.append([])  # epsilon
        self.regles[Aiprime] = newAiPrime

    def _term_greibach(self):
        """
        Si un terminal apparaît en position >=2, on le remplace par un NT dédié.
        """
        nouvelles_regles = {}
        for A, prod_list in self.regles.items():
            for seq in prod_list:
                # on ne touche pas seq[0] s'il est terminal (forme normal de greibach => c'est correct),
                # mais s'il y a un terminal en position 1,2,... => on remplace
                for i in range(1, len(seq)):
                    symb = seq[i]
                    if symb.islower():
                        # cherche NT existant
                        nt_equiv = None
                        for x, y in nouvelles_regles.items():
                            if y == [[symb]]:
                                nt_equiv = x
                                break
                        if not nt_equiv:
                            nt_equiv = self.genNT.suivant()
                            nouvelles_regles[nt_equiv] = [[symb]]
                        seq[i] = nt_equiv

        for nt, rhs in nouvelles_regles.items():
            if nt not in self.regles:
                self.regles[nt] = rhs

    def _final_placer_terminal_en_tete(self):
        """
        Dernière passe pour éviter qu'une règle commence par un NT.
        On substitue en boucle si seq[0] est un NT (et on sait que ce NT
        peut dériver un terminal). On limite le nombre d'itérations pour
        éviter les cycles infinis.
        """
        max_iter = 3 * len(self.regles) + 50
        changed = True
        while changed and max_iter > 0:
            changed = False
            max_iter -= 1
            for A in list(self.regles.keys()):
                new_list = []
                for seq in self.regles[A]:
                    if not seq:
                        new_list.append(seq)
                    elif seq[0].isupper():
                        # substituer
                        head = seq[0]
                        if head in self.regles:
                            # déplie toutes les alternatives
                            for alt in self.regles[head]:
                                new_list.append(alt + seq[1:])
                            changed = True
                        else:
                            # inconnu => on laisse
                            new_list.append(seq)
                    else:
                        new_list.append(seq)
                self.regles[A] = new_list

    def _valider_greibach(self):
        """
        Vérifie rapidement : si ce n'est pas epsilon (pour l'axiome),
        alors la règle doit commencer par un terminal.
        """
        for A, prods in self.regles.items():
            for seq in prods:
                if is_epsilon(seq):
                    # >>>>>> CHANGEMENT ICI <<<<<<
                    if A != self.axiome:
                        # remplacer "pas forme normale de chomsky" par "pas forme normale de greibach"
                        raise ValueError(f"{A} -> ε hors axiome => pas forme normale de greibach")
                else:
                    # doit commencer par un terminal
                    if not seq[0].islower():
                        raise ValueError(f"La règle {A} -> {''.join(seq)} "
                                        "ne commence pas par un terminal => pas forme normale de greibach")
                    
########################################
# MAIN
########################################
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grammaire.py <fichier.general>")
        sys.exit(1)

    fichier_entree = sys.argv[1]
    fichier_sortie_chom = fichier_entree.replace(".general", ".chomsky")
    fichier_sortie_grei = fichier_entree.replace(".general", ".greibach")

    # Chomsky
    g_chomsky = Grammaire()
    g_chomsky.lire(fichier_entree)
    g_chomsky.chomsky()
    g_chomsky.ecrire(fichier_sortie_chom)

    # Greibach
    g_greibach = Grammaire()
    g_greibach.lire(fichier_entree)
    try:
        g_greibach.greibach()
        g_greibach.ecrire(fichier_sortie_grei)
    except ValueError as e:
        print(f"Erreur forme normale de Greibach : {e}")
        # on force la création d'un .greibach vide
        with open(fichier_sortie_grei, "w") as f_out:
            pass