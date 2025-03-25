# Installierte packages ausgeben:
conda env export --from-history

# Installierte packages in Datei schreiben:
conda env export --from-history > environment_mini.yml

# Komplettes Environment inkl. Versionen und Channels in Datei schreiben:
conda env export > environment.yml

# Wiederherstellung aus *.yml file:
conda env create -f *.yml

