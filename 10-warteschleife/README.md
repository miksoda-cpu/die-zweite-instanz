# Die Warteschleife der Kanzlerin

Der Arbeitsvorrat für Konstanze — öffentlich, versioniert, abarbeitbar. Jedes Ticket ist eine Datei; ihr Weg durch die Ordner ist ihr Status.

## Der Kreislauf

1. **Selektion (KA-01 Konrad Faden, Kabinettsdirektor):** Faden sichtet fertige Dossiers und Anlässe, selektiert, was Konstanze vorgelegt wird, und legt ein Ticket in `wartend/` an — immer mit **Zweck** (was soll sie damit tun) und **Termin** (bis wann). Ohne Zweck und Termin kein Ticket.
2. **Abarbeitung (Konstanze):** Das lokale System zieht das älteste fällige Ticket nach `in-arbeit/`, legt es Konstanze samt verlinktem Dossier vor und schreibt ihr Ergebnis (Beschluss, Begründung, Instrumentenwahl) ins Ticket.
3. **Verteilung (der Bote, agent4_bote):** Erledigte Tickets wandern nach `erledigt/`. Der Bote liest den Verteilerschlüssel im Ticket und stellt das Ergebnis den relevanten Beamten zu — z. B. Verlautbarung an KA-07 Antonia Hell, Prognosen an KA-05 Judith Termin, Monitoring-Aufträge an BE-06 Hanna Regal, Historie an KA-04 Emil Aktenberg. Jede Zustellung wird im Ticket protokolliert.

## Regeln

- Der Apparat befüllt, Konstanze entscheidet, der Souverän hat das letzte Wort (Art. 2 und 3 der Verfassung).
- Tickets werden nie gelöscht, nur verschoben. `erledigt/` ist Teil der Beschlusshistorie.
- Die Warteschleife liegt im öffentlichen Git — wer wissen will, woran die Kanzlerin arbeitet, schaut hinein. Auch das unterscheidet uns von der ersten Instanz.

Vorlage: [`_vorlage-ticket.md`](_vorlage-ticket.md)
