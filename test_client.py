from client import Network

print("Pokúšam sa pripojiť na server...")
n = Network("127.0.0.1")

if n.player_id is not None:
    print(f"ÚSPECH! Pripojený k serveru. Moje pridelené ID je: {n.player_id}")
else:
    print("CHYBA: Nepodarilo sa pripojiť.")