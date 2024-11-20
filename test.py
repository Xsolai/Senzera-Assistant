import re
def remove_sources(text):
     # Use regex to match the pattern 【number:number†filename.extension】
    clean_text = re.sub(r"【\d+:\d+†[^\s]+】", "", text)
    # Remove any extra spaces left from the removal
    return ' '.join(clean_text.split())



text = """"

Das Waxing für den Po bei Senzera kostet regulär 22 Euro. Wenn du die S-Card besitzt, erhältst du einen Rabatt und zahlst nur 14 Euro【4:4†waxing.json】. 

Die S-Card bietet dir 30 % Rabatt auf alle regulären Behandlungen und kostet 132,80 Euro pro Jahr【4:0†waxing.json】. 

Du kannst mehr über unsere Waxing-Dienstleistungen auf unserer [Service-Seite](https://senzera.com/behandlungen/professionelle-haarentfernung-durch-waxing/) erfahren. Buche jetzt deinen Termin, um von unseren Angeboten zu profitieren!
"""

print(remove_sources(text))