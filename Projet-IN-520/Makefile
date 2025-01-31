# Make (remplacer le 3 par le nombre de lettres que vous voulez pour une grammaire)
run:
	python Grammaire.py test3.general
	python Generateur.py 3 exemple.chomsky
	python Generateur.py 3 exemple.greibach
	python Generateur.py 3 exemple.general

# Make diff
diff:
	python Generateur.py 3 exemple.chomsky > res_chomsky.txt
	python Generateur.py 3 exemple.greibach > res_greibach.txt
	python Generateur.py 3 exemple.general > res_general.txt
	diff res_chomsky.txt res_greibach.txt > diff_chomsky_greibach.txt || true
	diff res_chomsky.txt res_general.txt > diff_chomsky_general.txt || true
	diff res_greibach.txt res_general.txt > diff_greibach_general.txt || true
	@echo "Les diffs ont été sauvegardés dans diff_chomsky_greibach.txt, diff_chomsky_general.txt et diff_greibach_general.txt"
