# gnucash-importer

Damit ich mir das händische Kategorisieren eines CSV Import in mein GnuCash spare!

Ausgehend von einer bestehenden GnuCash Buchführung kann man sich damit die Arbeit erleichtern, indem
- automatisches importieren ausgehend von einem Bawag PSK Export CSV
- automatisches Kategorisieren der Buchungen ausgehend von bestehenden Buchungen

bestehende Buchungen einen Kontos (Account) werden dazu analysiert und die
Zeilen Beschreibung und Notizen werden zur Erkennung des Gegenkontos in einen Kategorisierer gefüttert.

Die damit erhaltenen Daten werden zu kategorisieren der neuen Buchungen im CSV File
herangezogen. Jeder Bucungs wird dabei einen Nummer (auch schon im CSV File) hinzugefügt,
sodass vermieden wird, einen Buchung doppelt zu importieren.

Ausgehend von der bestehenden GnuCash Datei
- gnucash_trainer.py - analysiert die bestehenden Buchungen und speichert den Status des Netzwerks in einer JSON Datei
- bawag_gnucash_import.py
    liest aus einem Verzeichnis mit Bawag Export CSV Files alle ein
    kategorisiert aufgrund der JSON Datei vom trainer
    importiert in GnuCash
- gnucash_verfier.py
    zeigt Buchungen die laut Netzwerk einen sehr geringen Score aufweisen
    vielleicht handelt es sich um eine Falsche Zuordnung
- Buchungen ggf. korrigieren, dann beginnt der Workflow wieder von vorn (trainer -> import -> verify)

Ein Backup der GnuCash Datei ist immer ratsam, bei läuft das aber recht reibungslos
