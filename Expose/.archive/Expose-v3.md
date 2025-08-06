# Polar Interpolation: Eine medienarchäologische Analyse von Inpainting-Algorithmen in equirectangularer 360°-Panoramaerstellung (2004-2024)

## Abstract (300 Wörter)

Diese Dissertation untersucht die technischen Operationen von Inpainting-Algorithmen bei der Vervollständigung polarer Singularitäten in equirectangularen 360°-Panoramen. Ausgehend von der Beobachtung, dass die Pole sphärischer Projektionen mathematische Unendlichkeitspunkte darstellen, analysiert die Arbeit, wie verschiedene algorithmische Ansätze diese Leerstellen "capturen" (Blas 2016) und durch interpolierte Bilddaten füllen. Die Forschung folgt einer practice-based methodology, die theoretische Konzepte zeitgenössischer Algorithmus-Studien als technische Analysemethoden operationalisiert.

Methodisch verbindet die Arbeit vier analytische Zugänge: (1) "Capture" als operative Logik untersucht, wie Algorithmen Lücken identifizieren und verarbeiten; (2) "Technological Inscription" (Benjamin 2019) macht Design-Entscheidungen in Code sichtbar; (3) "Sousveillance" (Browne 2015) entwickelt forensische Methoden zur Überwachung algorithmischer Operationen; (4) "Glitch Methodology" (Russell 2020) nutzt systematische Störungen als Erkenntnismethode.

Durch Reverse Engineering historischer Implementierungen (SIFT/SURF 2004-2010), forensische Analyse von PatchMatch-Verfahren (2010-2020) und experimentelle Störung neuronaler Inpainting-Systeme (2020-2024) zeigt die Arbeit, wie sich die Logik der Pol-Vervollständigung von geometrischer Feature-Detection über statistisches Pattern-Matching zu probabilistischer Bildgenerierung entwickelt hat. Die praktischen Experimente produzieren dabei nicht nur analytische Einsichten, sondern auch alternative Vervollständigungslogiken, die normative Annahmen über visuelle Kohärenz herausfordern.

Die Dissertation leistet drei Beiträge: (1) Eine technische Genealogie der Pol-Inpainting-Verfahren als medienarchäologisches Phänomen; (2) Eine practice-based methodology für kritische Algorithmus-Forschung, die Code als Primärquelle behandelt; (3) Experimentelle Counter-Inpainting-Verfahren, die alternative Formen sphärischer Bildvervollständigung ermöglichen. Damit positioniert sich die Arbeit an der Schnittstelle von Computer Vision, kritischen Algorithmus-Studien und experimenteller Medienpraxis, ohne dabei in explizite Politisierung zu verfallen, sondern durch rigorose technische Analyse die eingeschriebenen Logiken algorithmischer Bildproduktion offenzulegen.

## Gliederung des Exposés

### 1. Einleitung: Das polare Problem equirectangularer Projektion

#### 1.1. Technische Problemstellung: Mathematische Singularitäten an den Polen

**Frage:** Warum entstehen unvermeidbare Verzerrungen und Datenlücken an den Polen equirectangularer Projektionen?
**Literatur:** Snyder (1987) "Map Projections", Furuti (2006) "Cylindrical Projections"
**Technologie:** Equirectangular mapping, UV-Koordinatensysteme, Pol-Artefakte
**Argumentationsform:** Mathematisch-technische Problemanalyse

##### 1.1.1. Die Unendlichkeitspunkte der sphärischen Abbildung

**These:** Die Pole repräsentieren mathematische Singularitäten, wo ein Punkt auf unendlich viele Pixel gemappt wird
**Literatur:** Bourke (2006) "Spherical Projection", Kangro (2007) "Sphere Mapping Coordinates"
**Technologie:** Mathematische Analyse der Jacobi-Determinante an θ = 0, π
**Argumentationsform:** Deduktive mathematische Herleitung

##### 1.1.2. Historische Lösungsansätze: Von manueller Retusche zu algorithmischer Interpolation

**These:** Die Evolution von händischer Pol-Kaschierung zu automatisierten Verfahren markiert einen epistemischen Bruch
**Literatur:** Criminisi et al. (2004) "Region Filling", Barnes et al. (2009) "PatchMatch"
**Technologie:** Vergleich manueller Photoshop-Techniken mit frühen Algorithmen
**Argumentationsform:** Historische Kontrastierung

#### 1.2. Forschungsfrage: Wie "capturen" Algorithmen polare Leerstellen?

**Frage:** Welche operativen Logiken wenden verschiedene Inpainting-Algorithmen auf Pol-Singularitäten an?
**These:** Jeder Algorithmus implementiert eine spezifische "capture logic" (Blas 2016) für die Identifikation und Füllung polarer Regionen
**Literatur:** Blas (2016) "Contra-Internet", Chun (2011) "Programmed Visions"
**Argumentationsform:** Konzepttransfer von Critical Internet Studies zu Computer Vision

### 2. Theoretischer Rahmen: Algorithmus-Analyse als technische Praxis

#### 2.1. "Capture" als operative Logik algorithmischer Selektion

**Frage:** Wie lässt sich Zach Blas' Konzept des "capture" für die Analyse von Inpainting-Operationen fruchtbar machen?
**Literatur:** Blas (2016) "Contra-Internet", Blas (2014) "Queer Darkness"
**Technologie:** Analyse von Masking-, Selection- und Priority-Mechanismen in Inpainting
**Argumentationsform:** Methodische Abstraktion und Transfer

##### 2.1.1. Von Internet-Protokollen zu Bildverarbeitungs-Pipelines

**These:** "Capture" beschreibt präzise, wie Algorithmen aktiv Bildbereiche selektieren und verarbeiten
**Literatur:** Galloway (2004) "Protocol", Mackenzie (2017) "Machine Learners"
**Technologie:** Code-Analyse von OpenCV inpaint(), PatchMatch priority computation
**Argumentationsform:** Analogiebildung zwischen Netzwerk- und Bildprotokollen

##### 2.1.2. Capture-Mechanismen in drei Algorithmus-Generationen

**These:** SIFT "captured" Features, PatchMatch "captured" Patches, ML "captured" latente Repräsentationen
**Literatur:** Lowe (2004) "SIFT", Barnes et al. (2009) "PatchMatch", Rombach et al. (2022) "Stable Diffusion"
**Technologie:** Komparative Code-Analyse der Selektionsmechanismen
**Argumentationsform:** Empirische Kategorisierung

#### 2.2. Technological Inscription: Code als eingeschriebene Entscheidung

**Frage:** Wie materialisieren sich Design-Entscheidungen in Inpainting-Implementierungen?
**Literatur:** Benjamin (2019) "Race After Technology", Dourish (2017) "The Stuff of Bits"
**Argumentationsform:** Materialistisches Code-Reading

##### 2.2.1. Design Decisions in Pol-Behandlung: Threshold Values und Default Behaviors

**These:** Schwellwerte für Pol-Erkennung sind kulturell-technische Inscriptions
**Literatur:** Noble (2018) "Algorithms of Oppression", Crawford & Paglen (2019) "Excavating AI"
**Technologie:** Analyse von Default-Parametern in libvips, OpenCV, PIL
**Argumentationsform:** Critical Code Studies

##### 2.2.2. Die Politik der "Seamlessness": Welche Kontinuität wird eingeschrieben?

**These:** Die Präferenz für "nahtlose" Übergänge ist eine spezifische technokulturelle Wertentscheidung
**Literatur:** Nakamura (2007) "Digitizing Race", Chun (2006) "Control and Freedom"
**Technologie:** Analyse von Loss Functions in neuronalen Inpainting-Modellen
**Argumentationsform:** Dekonstruktion technischer Neutralität

#### 2.3. Sousveillance als forensische Methode

**Frage:** Wie kann Brownes Konzept der "Sousveillance" für Algorithmus-Überwachung operationalisiert werden?
**Literatur:** Browne (2015) "Dark Matters", Mann et al. (2003) "Sousveillance"
**Argumentationsform:** Methodentransfer von Surveillance Studies zu Algorithm Studies

##### 2.3.1. Den Algorithmus beobachten: Forensische Spurensicherung

**These:** Inpainting-Algorithmen hinterlassen charakteristische Artefakte, die forensisch analysierbar sind
**Literatur:** Farid (2016) "Photo Forensics", Agarwal et al. (2020) "Detecting Deep-Fake Videos"
**Technologie:** Frequenzanalyse, Noise Pattern Analysis, Statistical Anomaly Detection
**Argumentationsform:** Empirische Beweisführung

##### 2.3.2. Counter-Surveillance Tools für Inpainting-Detection

**These:** Sousveillance-Prinzipien ermöglichen die Entwicklung von Detection-Algorithmen
**Literatur:** Rossler et al. (2019) "FaceForensics++", Wang et al. (2020) "CNN-generated images detection"
**Technologie:** Entwicklung eigener Detection-Methoden für Pol-Inpainting
**Argumentationsform:** Konstruktive Methodenentwicklung

#### 2.4. Glitch als systematische Erkenntnismethode

**Frage:** Wie macht kontrollierte Störung algorithmische Operationen sichtbar?
**Literatur:** Russell (2020) "Glitch Feminism", Menkman (2011) "The Glitch Moment(um)"
**Argumentationsform:** Experimentelle Epistemologie

##### 2.4.1. Interruption Protocols: Inpainting-Prozesse unterbrechen

**These:** Systematische Unterbrechung verschiedener Pipeline-Stadien offenbart verborgene Operationen
**Literatur:** Mackenzie (2006) "Cutting Code", Fuller (2008) "Software Studies"
**Technologie:** Process Hooks, Memory Manipulation, Timing Attacks auf Inpainting
**Argumentationsform:** Experimentelle Verifikation

##### 2.4.2. Productive Failures: Wenn Pol-Inpainting "falsch" läuft

**These:** Algorithmus-Fehler sind epistemisch produktiv für das Verständnis normativer Annahmen
**Literatur:** Nunes (2011) "Error: Glitch, Noise, and Jam", Krapp (2011) "Noise Channels"
**Technologie:** Systematic Glitch Induction in COLMAP, Reality Capture, Metashape
**Argumentationsform:** Fehleranalyse als Erkenntnismethode

### 3. Stand der Forschung: Technische Innovation ohne kritische Reflexion

#### 3.1. Computer Vision: Pol-Inpainting als Optimierungsproblem

**Frage:** Wie behandelt die technische Literatur polare Singularitäten?
**Literatur:** Köppel et al. (2016) "Temporally Consistent Hole Filling", Huang et al. (2016) "360 Panorama Cloning"
**Argumentationsform:** Systematischer Literature Review

##### 3.1.1. Feature-basierte Ansätze (2004-2012)

**These:** Frühe Verfahren behandelten Pole als gewöhnliche Bildregionen ohne Berücksichtigung sphärischer Geometrie
**Literatur:** Brown & Lowe (2007) "Automatic Panoramic Image Stitching", Kopf et al. (2007) "Capturing and Viewing Gigapixel Images"
**Technologie:** SIFT, SURF, ORB Feature Detectors
**Argumentationsform:** Technische Genealogie

##### 3.1.2. Spherical-aware Inpainting (2013-2020)

**These:** Die Erkenntnis der sphärischen Topologie führte zu spezialisierten Pol-Algorithmen
**Literatur:** Akimoto et al. (2019) "360° Image Completion", Wei et al. (2020) "Spherical Image Inpainting"
**Technologie:** Cube Map Conversion, Spherical Harmonics
**Argumentationsform:** Paradigmenwechsel-Analyse

##### 3.1.3. Neural Approaches (2020-2024)

**These:** Deep Learning Modelle lernen implizit Pol-Vervollständigung ohne explizite geometrische Modellierung
**Literatur:** Wang et al. (2023) "PanoGAN", Li et al. (2024) "OmniDreamer"
**Technologie:** GANs, Diffusion Models, Vision Transformers
**Argumentationsform:** State-of-the-Art Synthese

#### 3.2. Critical Algorithm Studies: Die Lücke der visuellen Algorithmen

**Frage:** Warum fehlt kritische Analyse speziell für Bildverarbeitungs-Algorithmen?
**Literatur:** Seaver (2017) "Algorithms as Culture", Bucher (2018) "If...Then: Algorithmic Power"
**Argumentationsform:** Defizitanalyse

##### 3.2.1. Platform Studies Dominanz: Social Media über Computer Vision

**These:** Die Fokussierung auf Plattform-Algorithmen vernachlässigt Low-Level Bildoperationen
**Literatur:** Gillespie (2014) "Algorithm[method]", Rieder (2020) "Engines of Order"
**Technologie:** Gegenüberstellung Facebook EdgeRank vs. OpenCV Funktionen
**Argumentationsform:** Disziplinäre Blindstellen-Analyse

##### 3.2.2. Das Politische im scheinbar Technischen

**These:** Inpainting wird als "neutrale" Technik behandelt, obwohl normative Entscheidungen eingeschrieben sind
**Literatur:** Pasquale (2015) "The Black Box Society", O'Neil (2016) "Weapons of Math Destruction"
**Argumentationsform:** Ideologiekritik technischer Neutralität

#### 3.3. Practice-based Media Research: Ansätze und Grenzen

**Frage:** Wie können künstlerisch-praktische Methoden für Algorithmus-Forschung fruchtbar gemacht werden?
**Literatur:** Candy & Edmonds (2018) "Practice-Based Research", Borgdorff (2012) "The Conflict of the Faculties"
**Argumentationsform:** Methodologische Reflexion

##### 3.3.1. Artistic Research mit Algorithmen: Precedents

**These:** Künstler\*innen wie Paglen und Menkman bieten Modelle für practice-based Algorithm Studies
**Literatur:** Paglen (2019) "Sight Machine", Steyerl (2017) "Duty Free Art"
**Technologie:** ImageNet Roulette, Resolution Studies
**Argumentationsform:** Best Practice Analyse

##### 3.3.2. Die Herausforderung der technischen Tiefe

**These:** Practice-based Research muss technische Kompetenz mit kritischer Reflexion verbinden
**Literatur:** Cox & McLean (2013) "Speaking Code", Montfort et al. (2012) "10 PRINT"
**Argumentationsform:** Methodische Synthese

### 4. Methodologie: Vier Phasen practice-based Algorithm Research

#### 4.1. Phase 1: Algorithmic Archaeology der Pol-Behandlung (Monate 1-6)

**Frage:** Welche historischen Schichten lassen sich in aktuellen Pol-Inpainting-Verfahren freilegen?
**Literatur:** Parikka (2012) "What is Media Archaeology?", Ernst (2013) "Digital Memory"
**Technologie:** Git History Analysis, Legacy Code in OpenCV/GDAL
**Argumentationsform:** Archäologische Schichtung

##### 4.1.1. Code-Genealogie: Von geometrischer zu statistischer Pol-Füllung

**These:** Die Entwicklung zeigt drei distinkte Epochen mit je eigener Pol-Logik
**Literatur:** Fuller (2008) "Software Studies", Marino (2020) "Critical Code Studies"
**Technologie:** Historische Implementierungen: Hugin (2003), PTGui (2005), AutoStitch (2007)
**Argumentationsform:** Epochale Periodisierung

##### 4.1.2. Inscriptions sichtbar machen: Default Values und Hidden Assumptions

**These:** Magic Numbers und Schwellwerte offenbaren eingeschriebene Annahmen über "korrekte" Pole
**Literatur:** Benjamin (2019) "Race After Technology", Amaro (2019) "As If"
**Technologie:** Static Code Analysis, Parameter Archaeology
**Argumentationsform:** Close Reading von Code

#### 4.2. Phase 2: Sousveillance Implementation (Monate 7-18)

**Frage:** Wie können Inpainting-Operationen systematisch überwacht werden?
**Literatur:** Browne (2015) "Dark Matters", Farid (2016) "Photo Forensics"
**Technologie:** Custom Logging, Process Monitoring, Output Analysis
**Argumentationsform:** Konstruktive Methodenentwicklung

##### 4.2.1. Forensische Werkzeugentwicklung

**These:** Jeder Inpainting-Algorithmus hinterlässt einzigartige Pol-Signaturen
**Literatur:** Kirchner & Fridrich (2010) "On Detection of Median Filtering", Popescu & Farid (2005) "Statistical Tools"
**Technologie:** Fourier Analysis, Benford's Law, PRNU Analysis
**Argumentationsform:** Empirische Signaturentwicklung

##### 4.2.2. Real-time Algorithm Monitoring

**These:** Live-Überwachung von Inpainting-Prozessen ermöglicht tiefere Einblicke
**Literatur:** Introna (2016) "Algorithms, Governance, and Governmentality", Kitchin (2017) "Thinking Critically"
**Technologie:** eBPF Hooks, CUDA Profiling, Memory Tracing
**Argumentationsform:** Experimentelle Beobachtung

#### 4.3. Phase 3: Systematic Glitching Experiments (Monate 19-30)

**Frage:** Was offenbaren kontrollierte Störungen über normative Pol-Vervollständigung?
**Literatur:** Russell (2020) "Glitch Feminism", Cascone (2000) "The Aesthetics of Failure"
**Technologie:** Targeted Process Corruption, Parameter Fuzzing
**Argumentationsform:** Experimentelle Störungsanalyse

##### 4.3.1. Interruption Protocols für drei Algorithmus-Typen

**These:** Verschiedene Algorithmen reagieren charakteristisch auf spezifische Störungen
**Literatur:** Temkin (2014) "Glitched Literature", Berry (2012) "Critical Theory and the Digital"
**Technologie:** SIFT: Feature Corruption, PatchMatch: Priority Manipulation, Neural: Latent Space Intervention
**Argumentationsform:** Komparative Experimente

##### 4.3.2. Productive Failures: Alternative Pol-Ästhetiken

**These:** Glitches produzieren nicht nur Fehler, sondern alternative visuelle Logiken
**Literatur:** Menkman (2011) "Glitch Studies Manifesto", Kane (2019) "High-Tech Trash"
**Technologie:** Systematic Glitch Collection, Taxonomie entwickeln
**Argumentationsform:** Ästhetische Kategorisierung

#### 4.4. Phase 4: Counter-Inpainting Development (Monate 31-36)

**Frage:** Wie können alternative Pol-Vervollständigungslogiken implementiert werden?
**Literatur:** Blas (2016) "Contra-Internet", Galloway (2012) "The Interface Effect"
**Technologie:** Custom Algorithm Development, Speculative Implementations
**Argumentationsform:** Konstruktive Spekulation

##### 4.4.1. Drei spekulative Pol-Algorithmen

**These:** Jenseits normativer Seamlessness existieren multiple Möglichkeiten der Pol-Behandlung
**Literatur:** Dunne & Raby (2013) "Speculative Everything", Bratton (2016) "The Stack"
**Technologie:** (1) Void-Preserving Inpainting, (2) Glitch-Aesthetic Completion, (3) Multi-Reality Poles
**Argumentationsform:** Design Fiction Implementation

##### 4.4.2. Open Source Toolkit: "Polar Alternatives"

**These:** Alternative Implementierungen müssen zugänglich gemacht werden
**Literatur:** Kelty (2008) "Two Bits", Coleman (2013) "Coding Freedom"
**Technologie:** Python Library, WebGL Demo, Dokumentation
**Argumentationsform:** Praktische Intervention

### 5. Erwartete Ergebnisse: Theorie, Methode, Praxis

#### 5.1. Theoretischer Beitrag: Operative Pol-Logiken

**These:** Die Dissertation etabliert "Polar Interpolation" als eigene Kategorie algorithmischer Bildproduktion
**Literatur:** Synthesis eigener Forschung mit bestehender Theorie
**Argumentationsform:** Begriffsprägung und Definition

##### 5.1.1. Drei Modi polarer Capture-Logik

**These:** Geometrisch-restorative, statistisch-plausible und generativ-spekulative Pol-Behandlung
**Argumentationsform:** Typologieentwicklung

##### 5.1.2. Die Singularität als produktiver Ort

**These:** Mathematische Singularitäten sind keine Probleme, sondern Möglichkeitsräume
**Argumentationsform:** Philosophische Umwertung

#### 5.2. Methodologischer Beitrag: Practice-based Algorithm Studies

**These:** Die Verbindung von Code-Analyse, Forensik und experimenteller Störung konstituiert neue Methodologie
**Literatur:** Integration aller vier theoretischen Ansätze
**Argumentationsform:** Methodensynthese

##### 5.2.1. Vom Close Reading zum Close Coding

**These:** Algorithmen erfordern eigene hermeneutische Verfahren
**Argumentationsform:** Methodologische Innovation

##### 5.2.2. Experimentelle Verifikation als Standard

**These:** Theoretische Claims müssen durch Code-Experimente validiert werden
**Argumentationsform:** Wissenschaftstheoretische Positionierung

#### 5.3. Praktischer Output: Tools und Alternativen

**These:** Forschung muss verwendbare Alternativen produzieren
**Technologie:** Vollständige Toolchain von Analysis bis Alternative Implementation
**Argumentationsform:** Pragmatische Intervention

### 6. Zeitplan: 36 Monate strukturierte Forschung

#### 6.1. Jahr 1: Grundlagen und Analyse

**Monate 1-6:** Algorithmic Archaeology Phase
**Monate 7-12:** Begin Sousveillance Development
**Meilensteine:** Code-Genealogie komplett, erste forensische Tools

#### 6.2. Jahr 2: Experimente und Entwicklung

**Monate 13-18:** Complete Sousveillance Tools
**Monate 19-24:** Intensive Glitching Phase
**Meilensteine:** Forensisches Toolkit, Glitch-Taxonomie

#### 6.3. Jahr 3: Synthese und Dissemination

**Monate 25-30:** Complete Glitching, Begin Counter-Development
**Monate 31-36:** Finalize Alternative Implementations, Write Dissertation
**Meilensteine:** "Polar Alternatives" Toolkit, Dissertation, Ausstellung

### 7. Conclusio: Für eine kritische technische Praxis

#### 7.1. Die Notwendigkeit technisch informierter Kritik

**These:** Nur durch deep technical engagement können algorithmische Logiken verstanden werden
**Argumentationsform:** Methodologisches Plädoyer

#### 7.2. Ausblick: Weitere Singularitäten algorithmischer Bildproduktion

**Frage:** Welche anderen mathematischen Grenzfälle bergen kritisches Potenzial?
**Argumentationsform:** Prospektive Forschungsagenda

## Bibliografie

### Theoretische Grundlagen - Algorithmus-Analyse

- Amaro, Ramon (2019). _As If_. In: Uncertain Archives. Cambridge, MA: MIT Press.
- Benjamin, Ruha (2019). _Race After Technology: Abolitionist Tools for the New Jim Code_. Cambridge: Polity Press.
- Berry, David M. (2012). _Critical Theory and the Digital_. New York: Bloomsbury.
- Blas, Zach (2014). "Queer Darkness." In: _Dark Inquiry_, Rhizome.
- Blas, Zach (2016). _Contra-Internet_. [Artist Project & Texts]. https://zachblas.info/works/contra-internet/
- Borgdorff, Henk (2012). _The Conflict of the Faculties: Perspectives on Artistic Research and Academia_. Leiden: Leiden University Press.
- Bratton, Benjamin H. (2016). _The Stack: On Software and Sovereignty_. Cambridge, MA: MIT Press.
- Browne, Simone (2015). _Dark Matters: On the Surveillance of Blackness_. Durham: Duke University Press.
- Bucher, Taina (2018). _If...Then: Algorithmic Power and Politics_. Oxford: Oxford University Press.
- Candy, Linda & Edmonds, Ernest (2018). "Practice-Based Research in the Creative Arts." _Leonardo_, 51(1), 63-69.
- Cascone, Kim (2000). "The Aesthetics of Failure: 'Post-Digital' Tendencies in Contemporary Computer Music." _Computer Music Journal_, 24(4), 12-18.
- Chun, Wendy Hui Kyong (2006). _Control and Freedom: Power and Paranoia in the Age of Fiber Optics_. Cambridge, MA: MIT Press.
- Chun, Wendy Hui Kyong (2011). _Programmed Visions: Software and Memory_. Cambridge, MA: MIT Press.
- Coleman, E. Gabriella (2013). _Coding Freedom: The Ethics and Aesthetics of Hacking_. Princeton: Princeton University Press.
- Cox, Geoff & McLean, Alex (2013). _Speaking Code: Coding as Aesthetic and Political Expression_. Cambridge, MA: MIT Press.
- Crawford, Kate & Paglen, Trevor (2019). "Excavating AI: The Politics of Training Sets for Machine Learning." https://excavating.ai
- Dourish, Paul (2017). _The Stuff of Bits: An Essay on the Materialities of Information_. Cambridge, MA: MIT Press.
- Dunne, Anthony & Raby, Fiona (2013). _Speculative Everything: Design, Fiction, and Social Dreaming_. Cambridge, MA: MIT Press.
- Ernst, Wolfgang (2013). _Digital Memory and the Archive_. Minneapolis: University of Minnesota Press.
- Fuller, Matthew (Ed.) (2008). _Software Studies: A Lexicon_. Cambridge, MA: MIT Press.
- Fuller, Matthew & Weizman, Eyal (2021). _Investigative Aesthetics: Conflicts and Commons in the Politics of Truth_. London: Verso.
- Galloway, Alexander R. (2004). _Protocol: How Control Exists After Decentralization_. Cambridge, MA: MIT Press.
- Galloway, Alexander R. (2012). _The Interface Effect_. Cambridge: Polity Press.
- Gillespie, Tarleton (2014). "The Relevance of Algorithms." In: _Media Technologies: Essays on Communication, Materiality, and Society_. Cambridge, MA: MIT Press.
- Introna, Lucas D. (2016). "Algorithms, Governance, and Governmentality." _Science, Technology, & Human Values_, 41(1), 17-49.
- Kane, Carolyn L. (2019). _High-Tech Trash: Glitch, Noise, and Aesthetic Failure_. Oakland: University of California Press.
- Kelty, Christopher M. (2008). _Two Bits: The Cultural Significance of Free Software_. Durham: Duke University Press.
- Kitchin, Rob (2017). "Thinking Critically About and Researching Algorithms." _Information, Communication & Society_, 20(1), 14-29.
- Krapp, Peter (2011). _Noise Channels: Glitch and Error in Digital Culture_. Minneapolis: University of Minnesota Press.
- Mackenzie, Adrian (2006). _Cutting Code: Software and Sociality_. New York: Peter Lang.
- Mackenzie, Adrian (2017). _Machine Learners: Archaeology of a Data Practice_. Cambridge, MA: MIT Press.
- Mann, Steve, Nolan, Jason & Wellman, Barry (2003). "Sousveillance: Inventing and Using Wearable Computing Devices." _Surveillance & Society_, 1(3), 331-355.
- Marino, Mark C. (2020). _Critical Code Studies_. Cambridge, MA: MIT Press.
- Menkman, Rosa (2011). _The Glitch Moment(um)_. Amsterdam: Institute of Network Cultures.
- Montfort, Nick et al. (2012). _10 PRINT CHR$(205.5+RND(1)); : GOTO 10_. Cambridge, MA: MIT Press.
- Nakamura, Lisa (2007). _Digitizing Race: Visual Cultures of the Internet_. Minneapolis: University of Minnesota Press.
- Noble, Safiya Umoja (2018). _Algorithms of Oppression: How Search Engines Reinforce Racism_. New York: NYU Press.
- Nunes, Mark (Ed.) (2011). _Error: Glitch, Noise, and Jam in New Media Cultures_. New York: Continuum.
- O'Neil, Cathy (2016). _Weapons of Math Destruction: How Big Data Increases Inequality and Threatens Democracy_. New York: Crown.
- Paglen, Trevor (2019). "Sight Machine." Installation/Software. https://paglen.studio
- Parikka, Jussi (2012). _What is Media Archaeology?_ Cambridge: Polity Press.
- Pasquale, Frank (2015). _The Black Box Society: The Secret Algorithms That Control Money and Information_. Cambridge, MA: Harvard University Press.
- Rieder, Bernhard (2020). _Engines of Order: A Mechanology of Algorithmic Techniques_. Amsterdam: Amsterdam University Press.
- Russell, Legacy (2020). _Glitch Feminism: A Manifesto_. London: Verso.
- Seaver, Nick (2017). "Algorithms as Culture: Some Tactics for the Ethnography of Algorithmic Systems." _Big Data & Society_, 4(2).
- Steyerl, Hito (2017). _Duty Free Art: Art in the Age of Planetary Civil War_. London: Verso.
- Temkin, Daniel (2014). "Glitched Literature." _NOOART: The Journal of Objectless Art_, 1.

### Technische Literatur - Panorama und Inpainting

- Agarwal, Shruti et al. (2020). "Detecting Deep-Fake Videos from Appearance and Behavior." _IEEE WIFS_.
- Akimoto, Naofumi et al. (2019). "360° Image Completion by Two-stage Conditional GANs." _IEEE ICIP_, 4704-4708.
- Barnes, Connelly, Shechtman, Eli, Finkelstein, Adam & Goldman, Dan B. (2009). "PatchMatch: A Randomized Correspondence Algorithm for Structural Image Editing." _ACM Transactions on Graphics_, 28(3).
- Bertalmio, Marcelo, Sapiro, Guillermo, Caselles, Vincent & Ballester, Coloma (2000). "Image Inpainting." _Proceedings of SIGGRAPH 2000_, 417-424.
- Bourke, Paul (2006). "Spherical Projection." http://paulbourke.net/geometry/transformationprojection/
- Brown, Matthew & Lowe, David G. (2007). "Automatic Panoramic Image Stitching using Invariant Features." _International Journal of Computer Vision_, 74(1), 59-73.
- Criminisi, Antonio, Pérez, Patrick & Toyama, Kentaro (2004). "Region Filling and Object Removal by Exemplar-Based Image Inpainting." _IEEE Transactions on Image Processing_, 13(9), 1200-1212.
- Efros, Alexei A. & Leung, Thomas K. (1999). "Texture Synthesis by Non-parametric Sampling." _Proceedings of IEEE ICCV_, 1033-1038.
- Farid, Hany (2016). _Photo Forensics_. Cambridge, MA: MIT Press.
- Furuti, Carlos A. (2006). "Cylindrical Projections." http://www.progonos.com/furuti/MapProj/Normal/ProjCyl/projCyl.html
- Huang, Jia-Bin et al. (2016). "360 Panorama Cloning on Sphere." _Visual Communications and Image Processing_.
- Kangro, Martin (2007). "Sphere Mapping Coordinates." _Technical Report_, Uppsala University.
- Kirchner, Matthias & Fridrich, Jessica (2010). "On Detection of Median Filtering in Digital Images." _Proceedings of SPIE_, 7541.
- Köppel, M., Makhlouf, M. B., Müller, K. & Ndjiki-Nya, P. (2016). "Temporally Consistent Adaptive Depth Map Preprocessing for View Synthesis." _IEEE VCIP_.
- Kopf, Johannes et al. (2007). "Capturing and Viewing Gigapixel Images." _ACM Transactions on Graphics_, 26(3).
- Li, Yuheng et al. (2024). "OmniDreamer: Towards Unified Generation of Omnidirectional Images." _Preprint_.
- Lowe, David G. (2004). "Distinctive Image Features from Scale-Invariant Keypoints." _International Journal of Computer Vision_, 60(2), 91-110.
- Popescu, Alin C. & Farid, Hany (2005). "Statistical Tools for Digital Forensics." _Information Hiding_, 128-147.
- Rombach, Robin et al. (2022). "High-Resolution Image Synthesis with Latent Diffusion Models." _Proceedings of CVPR_.
- Rossler, Andreas et al. (2019). "FaceForensics++: Learning to Detect Manipulated Facial Images." _Proceedings of ICCV_.
- Snyder, John P. (1987). _Map Projections - A Working Manual_. Washington: U.S. Geological Survey.
- Wang, Ting-Chun et al. (2020). "CNN-generated images are surprisingly easy to spot... for now." _Proceedings of CVPR_.
- Wang, Xu et al. (2023). "PanoGAN: Unsupervised Panorama Generation from Spherical Image Pairs." _IEEE VR_.
- Wei, Yinda et al. (2020). "Spherical Image Inpainting with Frame Transformation and Data-driven Prior Deep Networks." _Proceedings of ICPR_.

### Methodologie und Practice-Based Research

- Biggs, Michael & Büchler, Daniela (2011). "Communities, Values, Conventions and Actions." In: _The Routledge Companion to Research in the Arts_. London: Routledge.
- Bolt, Barbara (2016). "Artistic Research: A Performative Paradigm?" _Parse Journal_, 3, 129-142.
- Busch, Kathrin (2009). "Artistic Research and the Poetics of Knowledge." _Art & Research_, 2(2).
- Haseman, Brad (2006). "A Manifesto for Performative Research." _Media International Australia_, 118(1), 98-106.
- Nelson, Robin (2013). _Practice as Research in the Arts: Principles, Protocols, Pedagogies, Resistances_. Basingstoke: Palgrave Macmillan.
- Sullivan, Graeme (2010). _Art Practice as Research: Inquiry in Visual Arts_. Thousand Oaks: SAGE.
