
import requests

# Identitas Firebase
MY_PROJECT_ID = "dwh-unipdu-4124027"
NIM_ANDA = "4124027"  # Sesuaikan jika berbeda dengan NIM asli

# Data transaksi dummy yang berbeda dari contoh dosen
dummy_transaksi_mentah = [
    {
        "id_pesanan_nk": f"ORD-{4124027}-11",
        "tanggal_penjualan": "2026-03-08",
        "id_produk_nk": "PRD-002",
        "id_pelanggan_nk": f"CUST-{4124027}-11",
        "nama_pelanggan": "rahma putri lestari",
        "jenis_kelamin": "P",
        "tanggal_lahir": "1998-07-16",
        "alamat": "Jl. Pahlawan No. 27",
        "nama_kota": "surabaya",
        "nama_provinsi": "jatim",
        "id_kurir_nk": "KUR-04",
        "id_metode_bayar_nk": "PAY-03",
        "jumlah": 2,
        "harga_satuan": 175000,
        "diskon_persen": "8%",
        "ongkos_kirim": 16000
    },
    {
        "id_pesanan_nk": f"ORD-{4124027}-12",
        "tanggal_penjualan": "2026-06-17",
        "id_produk_nk": "PRD-003",
        "id_pelanggan_nk": f"CUST-{4124027}-12",
        "nama_pelanggan": "DIMAS ADITYA",
        "jenis_kelamin": "Pria",
        "tanggal_lahir": "2001-02-09",
        "alamat": "Jl. Ahmad Yani No. 41",
        "nama_kota": "malang",
        "nama_provinsi": "jatim",
        "id_kurir_nk": "KUR-02",
        "id_metode_bayar_nk": "PAY-04",
        "jumlah": -3,
        "harga_satuan": 1650000,
        "diskon_persen": "12%",
        "ongkos_kirim": 22000
    },
    {
        "id_pesanan_nk": f"ORD-{4124027}-13",
        "tanggal_penjualan": "2026-09-25",
        "id_produk_nk": "PRD-005",
        "id_pelanggan_nk": f"CUST-{4124027}-13",
        "nama_pelanggan": "naufal rizky pratama",
        "jenis_kelamin": "Cowok",
        "tanggal_lahir": "1987-12-04",
        "alamat": "Jl. Sudirman No. 63",
        "nama_kota": "pekanbaru",
        "nama_provinsi": "riau",
        "id_kurir_nk": "KUR-03",
        "id_metode_bayar_nk": "PAY-01",
        "jumlah": 4,
        "harga_satuan": 980000,
        "diskon_persen": "7%",
        "ongkos_kirim": 30000
    }
]


def dict_to_firestore(data_dict):
    fields = {}

    for key, value in data_dict.items():
        if isinstance(value, int):
            fields[key] = {"integerValue": str(value)}
        elif isinstance(value, float):
            fields[key] = {"doubleValue": value}
        else:
            fields[key] = {"stringValue": str(value)}

    return {"fields": fields}


if __name__ == "__main__":
    print(f"Mengunggah data ke Firebase: {MY_PROJECT_ID}")

    base_url = (
        f"https://firestore.googleapis.com/v1/projects/"
        f"{MY_PROJECT_ID}/databases/(default)/documents"
    )

    for row in dummy_transaksi_mentah:
        doc_id = row["id_pesanan_nk"]
        url = f"{base_url}/transaksi_mentah/{doc_id}"

        try:
            response = requests.patch(
                url,
                json=dict_to_firestore(row),
                timeout=15
            )

            if response.status_code == 200:
                print(f"[BERHASIL] {doc_id} tersimpan")
            else:
                print(
                    f"[GAGAL] {doc_id}: "
                    f"{response.status_code} - {response.text}"
                )

        except requests.RequestException as error:
            print(f"[ERROR] {doc_id}: {error}")
