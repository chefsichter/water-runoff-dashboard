Hier ist eine detaillierte Erklärung zu jeder Variablen aus deiner Tabelle auf **Deutsch**:

---

### **Hydrologische & Meteorologische Variablen** 🌧️💧🌡️

| **Variablenname** | **Bedeutung & Erklärung** |
|------------------|-------------------------|
| **P** | **Niederschlag (Precipitation)** – Gemessene tägliche Niederschlagsmenge in mm pro Tag. Die Daten stammen von MeteoSwiss und wurden auf Einzugsgebietsebene aggregiert. |
| **Qmm_mod** | **Abfluss (Runoff, CH-RUN)** – Abflussmenge (in mm pro Tag) aus dem hydrologischen Modell CH-RUN v1.0. |
| **Qmm_prevah** | **Abfluss (Runoff, PREVAH)** – Abflussmenge (in mm pro Tag) aus dem hydrologischen Modell PREVAH des WSL. |
| **T** | **Lufttemperatur (Air Temperature)** – Gemessene Lufttemperatur in Grad Celsius (°C). Die Daten stammen von MeteoSwiss und wurden auf Einzugsgebietsebene aggregiert. |

---

### **Topographische & Bodenbezogene Variablen** 🏔️🌱

| **Variablenname** | **Bedeutung & Erklärung** |
|------------------|-------------------------|
| **abb** | **Boden-Topographie-Index** – Ein Index, der die Beziehung zwischen Bodenfeuchte und Topographie beschreibt. |
| **area** | **Einzugsgebietsfläche** – Die Fläche eines hydrologischen Einzugsgebiets in Quadratmetern (m²). |
| **atb** | **Hydraulisch-Topographischer Index** – Ein Maß für die hydraulischen Eigenschaften des Bodens in Bezug auf die Topographie. |
| **btk** | **Bodentiefe (Soil Depth)** – Die Tiefe des Bodens in Metern (m), basierend auf SoilGrids und hochauflösenden Bodenkarten der Schweiz. |
| **dhm** | **Höhe (Elevation)** – Die mittlere Höhe des Einzugsgebiets über dem Meeresspiegel in Metern (m a.s.l.), basierend auf swisstopo. |
| **glm** | **Gletscher-Morphologie** – Eine Beschreibung der Gletscherbedeckung und -struktur innerhalb des Einzugsgebiets, basierend auf SGI2016. |
| **kwt** | **Hydraulische Leitfähigkeit (Hydraulic Conductivity)** – Die Fähigkeit des Bodens, Wasser durchzulassen, angegeben in mm pro Stunde (mm h⁻¹). |
| **pfc** | **Wasserspeicherkapazität des Bodens** – Der Anteil des Bodens, der Wasser speichern kann, angegeben in Prozent (%). |
| **slp** | **Hangneigung (Slope)** – Der durchschnittliche Neigungswinkel des Geländes in Grad (°). |

---

### **Landbedeckung & Nutzungstypen** 🌾🌳🏡

Diese Variablen geben den Anteil bestimmter Landnutzungstypen in einem Einzugsgebiet an. Die Werte liegen zwischen 0 und 1 (Fraktion), wobei 1 bedeutet, dass die gesamte Fläche von dieser Landbedeckung dominiert wird.

| **Variablenname** | **Bedeutung & Erklärung** |
|------------------|-------------------------|
| **frac_water** | **Wasserflächenanteil** – Der Anteil der Wasserflächen im Einzugsgebiet (Seen, Flüsse, Feuchtgebiete). |
| **frac_urban_areas** | **Städtischer Flächenanteil** – Anteil der Fläche, die durch urbane Gebiete (Häuser, Straßen, Industrie) bedeckt ist. |
| **frac_coniferous_forests** | **Nadelwaldanteil** – Anteil der Fläche, die von Nadelwäldern (Fichten, Kiefern, Tannen) bedeckt ist. |
| **frac_deciduous_forests** | **Laubwaldanteil** – Anteil der Fläche, die von Laubwäldern (Eichen, Buchen, Ahorn) bedeckt ist. |
| **frac_mixed_forests** | **Mischwaldanteil** – Anteil der Fläche, die von einer Mischung aus Laub- und Nadelwäldern bedeckt ist. |
| **frac_cereals** | **Getreideanbauanteil** – Anteil der Fläche, die für den Anbau von Getreide genutzt wird. |
| **frac_pasture** | **Weideflächenanteil** – Anteil der Fläche, die für Viehweiden genutzt wird. |
| **frac_bush** | **Buschanteil** – Anteil der Fläche, die von Sträuchern und Gebüschen bedeckt ist. |
| **frac_unknown** | **Unbekannter Flächenanteil** – Anteil der Fläche, der keiner bekannten Kategorie zugeordnet werden konnte. |
| **frac_firn** | **Firnanteil** – Anteil der Fläche, die mit Firn (zwischen Schnee und Gletschereis) bedeckt ist. |
| **frac_bare_ice** | **Gletscher-Eis-Anteil** – Anteil der Fläche, die von Gletschereis bedeckt ist. |
| **frac_rock** | **Felsanteil** – Anteil der Fläche, die von nacktem Fels bedeckt ist. |
| **frac_vegetables** | **Gemüseanbauanteil** – Anteil der Fläche, die für den Gemüseanbau genutzt wird. |
| **frac_alpine_vegetation** | **Alpine Vegetation** – Anteil der Fläche, die von alpiner Vegetation bedeckt ist (z. B. Hochgebirgspflanzen). |
| **frac_wetlands** | **Feuchtgebiete** – Anteil der Fläche, die aus Mooren oder Feuchtgebieten besteht. |
| **frac_sub_Alpine_meadow** | **Subalpine Wiesen** – Anteil der Fläche, die aus subalpinen Wiesen besteht. |
| **frac_alpine_meadow** | **Alpine Wiesen** – Anteil der Fläche, die aus alpinen Wiesen besteht. |
| **frac_bare_soil_vegetation** | **Vegetationsarme Böden** – Anteil der Fläche mit wenig oder keiner Vegetation. |
| **frac_grapes** | **Weinbauanteil** – Anteil der Fläche, die für den Weinbau genutzt wird. |

---

### **Sonstige Variablen** ⏳📊

| **Variablenname** | **Bedeutung & Erklärung** |
|------------------|-------------------------|
| **hru** | **Hydrologische Recheneinheit (Hydrologic Response Unit, HRU)** – Eine Unterteilung des Einzugsgebiets in kleinere Berechnungseinheiten. |
| **time** | **Zeit** – Zeitstempel der Daten (z. B. täglich, monatlich), gespeichert als `datetime64[ns]`. |

---

### **Zusammenfassung**
🔹 **Meteorologische Daten**: Niederschlag, Temperatur  
🔹 **Hydrologische Daten**: Abflussmengen  
🔹 **Topographie & Boden**: Höhe, Bodeneigenschaften, Hangneigung  
🔹 **Landnutzung**: Wälder, Gletscher, urbane Flächen, Landwirtschaft  

Hoffe, das hilft! 😊 Falls du noch Fragen hast oder eine spezielle Erklärung brauchst, sag einfach Bescheid! 🚀