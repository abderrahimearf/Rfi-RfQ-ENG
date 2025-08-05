from extract_doc import process_file

# Personnaliser la taille des chunks
chunks = process_file(
    file_path=r"C:\Users\DHM\Downloads\Proposition_Solution_Technique_MarocData.pdf",
    max_chars=700,
    overlap_chars=100
)

for c in chunks:
    print(f"{c['indexchunk']:03d} - Page {c['page']} - {len(c['contenu'])} caractères")
    print(c['contenu'])