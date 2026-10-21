
import requests
import time
import hashlib
from datetime import datetime, date

# =========================================================
# 1. KONFIGURASI
# =========================================================
MY_PROJECT_ID = "dwh-unipdu-4124027"

# Untuk sementara gunakan project milik sendiri.
# Tambahkan Project ID teman jika sudah mendapat izin.
TARGET_SOURCE_PROJECTS = [
    "dwh-unipdu-4124027"
]

# =========================================================
# 2. MASTER PRODUK
# =========================================================
MASTER_PRODUK = {
    "PRD-001": {
        "sk": 1, "nama": "Laptop ProBook 14",
        "merek": "TechBrand", "harga_dasar": 8500000,
        "kat": "Laptop", "induk": "Komputer & Aksesoris",
        "sup": "PT Mitra Komputindo", "kota_sup": "Jakarta"
    },
    "PRD-002": {
        "sk": 2, "nama": "Mouse Wireless M20",
        "merek": "ClickGear", "harga_dasar": 120000,
        "kat": "Aksesoris PC", "induk": "Komputer & Aksesoris",
        "sup": "CV Jaya Abadi", "kota_sup": "Surabaya"
    },
    "PRD-003": {
        "sk": 3, "nama": "Monitor LED 24 Inch",
        "merek": "VisionPlus", "harga_dasar": 1650000,
        "kat": "Monitor", "induk": "Komputer & Aksesoris",
        "sup": "PT Mitra Komputindo", "kota_sup": "Jakarta"
    },
    "PRD-004": {
        "sk": 4, "nama": "Mechanical Keyboard RGB",
        "merek": "KeyTech", "harga_dasar": 350000,
        "kat": "Keyboard", "induk": "Komputer & Aksesoris",
        "sup": "CV Jaya Abadi", "kota_sup": "Surabaya"
    },
    "PRD-005": {
        "sk": 5, "nama": "SSD NVMe 1TB Gen4",
        "merek": "FlashCore", "harga_dasar": 950000,
        "kat": "Storage", "induk": "Komponen PC",
        "sup": "PT Nusantara Data", "kota_sup": "Bandung"
    }
}

MASTER_KURIR = {
    "KUR-01": {"sk": 1, "nama": "JNE", "layanan": "Reguler"},
    "KUR-02": {"sk": 2, "nama": "SiCepat", "layanan": "BEST"},
    "KUR-03": {"sk": 3, "nama": "J&T Express", "layanan": "Ekonomi"},
    "KUR-04": {"sk": 4, "nama": "Pos Indonesia", "layanan": "Kilat Khusus"}
}

MASTER_BAYAR = {
    "PAY-01": {"sk": 1, "nama": "QRIS", "jenis": "E-Wallet"},
    "PAY-02": {"sk": 2, "nama": "BCA Virtual Account", "jenis": "Transfer Bank"},
    "PAY-03": {"sk": 3, "nama": "GoPay", "jenis": "E-Wallet"},
    "PAY-04": {"sk": 4, "nama": "Mandiri Virtual Account", "jenis": "Transfer Bank"}
}

# =========================================================
# 3. FUNGSI TRANSFORMASI
# =========================================================
def transform_gender(val):
    v = str(val).strip().lower()

    if v in ["l", "laki-laki", "laki", "pria", "cowok", "male", "m"]:
        return "Laki-laki"
    if v in ["p", "perempuan", "wanita", "cewek", "female", "f"]:
        return "Perempuan"

    return "Tidak Diketahui"


def transform_provinsi_dan_pulau(prov_raw):
    p = str(prov_raw).strip().lower()

    mapping = {
        "jatim": ("Jawa Timur", "Jawa"),
        "jawa timur": ("Jawa Timur", "Jawa"),
        "jateng": ("Jawa Tengah", "Jawa"),
        "jawa tengah": ("Jawa Tengah", "Jawa"),
        "jabar": ("Jawa Barat", "Jawa"),
        "jawa barat": ("Jawa Barat", "Jawa"),
        "dki": ("DKI Jakarta", "Jawa"),
        "jakarta": ("DKI Jakarta", "Jawa"),
        "diy": ("DI Yogyakarta", "Jawa"),
        "yogyakarta": ("DI Yogyakarta", "Jawa"),
        "banten": ("Banten", "Jawa"),
        "sumut": ("Sumatera Utara", "Sumatera"),
        "sumatera utara": ("Sumatera Utara", "Sumatera"),
        "sumbar": ("Sumatera Barat", "Sumatera"),
        "sumsel": ("Sumatera Selatan", "Sumatera"),
        "bali": ("Bali", "Bali & Nusa Tenggara"),
        "kaltim": ("Kalimantan Timur", "Kalimantan"),
        "kalsel": ("Kalimantan Selatan", "Kalimantan"),
        "sulsel": ("Sulawesi Selatan", "Sulawesi"),
        "riau": ("Riau", "Sumatera")
    }

    return mapping.get(p, (str(prov_raw).title(), "Indonesia Lainnya"))


def transform_kelompok_usia(tgl_lahir_str):
    tgl_lahir = datetime.strptime(
        tgl_lahir_str, "%Y-%m-%d"
    ).date()

    hari_ini = date.today()
    usia = hari_ini.year - tgl_lahir.year

    if (hari_ini.month, hari_ini.day) < (
        tgl_lahir.month, tgl_lahir.day
    ):
        usia -= 1

    if usia <= 25:
        return "Remaja/Muda (<=25)"
    if usia <= 35:
        return "Dewasa Muda (26-35)"
    if usia <= 50:
        return "Dewasa (36-50)"

    return "Lansia (>50)"


def transform_diskon_rupiah(diskon_raw, harga_bruto):
    teks = str(diskon_raw).strip()

    if "%" in teks:
        persen = float(teks.replace("%", "")) / 100
        return int(harga_bruto * persen)

    return int(float(teks))


# =========================================================
# 4. KOMUNIKASI FIRESTORE
# =========================================================
def dict_to_firestore(data_dict):
    fields = {}

    for key, value in data_dict.items():
        if isinstance(value, bool):
            fields[key] = {"booleanValue": value}
        elif isinstance(value, int):
            fields[key] = {"integerValue": str(value)}
        elif isinstance(value, float):
            fields[key] = {"doubleValue": value}
        else:
            fields[key] = {"stringValue": str(value)}

    return {"fields": fields}


def parse_firestore_doc(doc):
    clean = {}

    for key, value in doc.get("fields", {}).items():
        if "integerValue" in value:
            clean[key] = int(value["integerValue"])
        elif "doubleValue" in value:
            clean[key] = float(value["doubleValue"])
        elif "stringValue" in value:
            clean[key] = value["stringValue"]
        elif "booleanValue" in value:
            clean[key] = value["booleanValue"]

    return clean


def firestore_url(project_id, collection=None, doc_id=None):
    base = (
        "https://firestore.googleapis.com/v1/projects/"
        f"{project_id}/databases/(default)/documents"
    )

    if collection:
        base += f"/{collection}"
    if doc_id:
        base += f"/{doc_id}"

    return base


def upsert_firestore(collection, doc_id, data):
    url = firestore_url(MY_PROJECT_ID, collection, doc_id)

    response = requests.patch(
        url, json=dict_to_firestore(data), timeout=20
    )
    response.raise_for_status()


def get_collection(project_id, collection):
    url = firestore_url(project_id, collection)
    documents = []
    page_token = None

    while True:
        params = {"pageSize": 1000}
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        result = response.json()

        documents.extend(result.get("documents", []))
        page_token = result.get("nextPageToken")

        if not page_token:
            break

    return documents


# =========================================================
# 5. EXTRACT DAN LOAD KE LANDING ZONE
# =========================================================
def extract_and_load_to_landing_zone():
    print("\n=== EXTRACT & LOAD KE LANDING ZONE ===")

    now = datetime.now()
    partition_path = (
        f"orders/year={now:%Y}/month={now:%m}/day={now:%d}"
    )

    for source_pid in TARGET_SOURCE_PROJECTS:
        try:
            docs = get_collection(source_pid, "transaksi_mentah")

            for doc in docs:
                row = parse_firestore_doc(doc)

                if "id_pesanan_nk" not in row:
                    print("[LEWATI] Dokumen tidak memiliki ID pesanan")
                    continue

                row["sumber_project"] = source_pid
                row["partition_path"] = partition_path

                # Tambahkan sumber ke ID agar pesanan antarproject
                # tidak saling menimpa jika ID-nya sama.
                landing_id = (
                    source_pid + "_" + row["id_pesanan_nk"]
                )

                upsert_firestore(
                    "landing_zone_raw", landing_id, row
                )

            print(
                f"[BERHASIL] {len(docs)} dokumen dari {source_pid}"
            )

        except (requests.RequestException, ValueError) as error:
            print(f"[GAGAL] {source_pid}: {error}")


# =========================================================
# 6. TRANSFORM KE SKEMA BINTANG
# =========================================================
def transform_landing_to_star_schema():
    print("\n=== TRANSFORMASI KE SKEMA BINTANG ===")

    docs = get_collection(MY_PROJECT_ID, "landing_zone_raw")

    nama_hari = [
        "Senin", "Selasa", "Rabu", "Kamis",
        "Jumat", "Sabtu", "Minggu"
    ]
    nama_bulan = [
        "", "Januari", "Februari", "Maret", "April",
        "Mei", "Juni", "Juli", "Agustus", "September",
        "Oktober", "November", "Desember"
    ]

    for doc in docs:
        row = parse_firestore_doc(doc)

        try:
            dt = datetime.strptime(
                row["tanggal_penjualan"], "%Y-%m-%d"
            )
            kd_prd = row.get("id_produk_nk", "PRD-001")
            kd_kur = row.get("id_kurir_nk", "KUR-01")
            kd_byr = row.get("id_metode_bayar_nk", "PAY-01")

            if kd_prd not in MASTER_PRODUK:
                raise ValueError(f"Kode produk tidak dikenal: {kd_prd}")
            if kd_kur not in MASTER_KURIR:
                raise ValueError(f"Kode kurir tidak dikenal: {kd_kur}")
            if kd_byr not in MASTER_BAYAR:
                raise ValueError(f"Kode pembayaran tidak dikenal: {kd_byr}")

            # Dimensi waktu
            sk_waktu = int(dt.strftime("%Y%m%d"))

            upsert_firestore("dim_waktu", str(sk_waktu), {
                "sk_waktu": sk_waktu,
                "tanggal_penjualan": row["tanggal_penjualan"],
                "hari": dt.day,
                "bulan": dt.month,
                "nama_bulan": nama_bulan[dt.month],
                "kuartal": f"Q{(dt.month - 1) // 3 + 1}",
                "tahun": dt.year,
                "nama_hari": nama_hari[dt.weekday()]
            })

            # Dimensi produk
            produk = MASTER_PRODUK[kd_prd]
            sk_produk = produk["sk"]

            upsert_firestore("dim_produk", str(sk_produk), {
                "sk_produk": sk_produk,
                "id_produk_nk": kd_prd,
                "nama_produk": produk["nama"],
                "merek": produk["merek"],
                "harga_dasar": produk["harga_dasar"],
                "nama_kategori": produk["kat"],
                "nama_kategori_induk": produk["induk"],
                "nama_supplier": produk["sup"],
                "kota_supplier": produk["kota_sup"]
            })

            # Dimensi pelanggan
            id_pelanggan = row["id_pelanggan_nk"]
            sk_pelanggan = int(
                hashlib.md5(id_pelanggan.encode()).hexdigest()[:6], 16
            )

            provinsi, pulau = transform_provinsi_dan_pulau(
                row.get("nama_provinsi", "")
            )

            upsert_firestore("dim_pelanggan", str(sk_pelanggan), {
                "sk_pelanggan": sk_pelanggan,
                "id_pelanggan_nk": id_pelanggan,
                "nama_pelanggan": row["nama_pelanggan"].strip().title(),
                "jenis_kelamin": transform_gender(row["jenis_kelamin"]),
                "tanggal_lahir": row["tanggal_lahir"],
                "kelompok_usia": transform_kelompok_usia(
                    row["tanggal_lahir"]
                ),
                "alamat": row["alamat"],
                "nama_kota": row["nama_kota"].strip().title(),
                "nama_provinsi": provinsi,
                "pulau": pulau
            })

            # Dimensi kurir
            kurir = MASTER_KURIR[kd_kur]
            upsert_firestore("dim_kurir", str(kurir["sk"]), {
                "sk_kurir": kurir["sk"],
                "id_kurir_nk": kd_kur,
                "nama_kurir": kurir["nama"],
                "jenis_layanan": kurir["layanan"]
            })

            # Dimensi metode pembayaran
            bayar = MASTER_BAYAR[kd_byr]
            upsert_firestore(
                "dim_metode_bayar", str(bayar["sk"]), {
                    "sk_metode_bayar": bayar["sk"],
                    "id_metode_bayar_nk": kd_byr,
                    "nama_metode": bayar["nama"],
                    "jenis_metode": bayar["jenis"]
                }
            )

            # Fakta penjualan
            jumlah = abs(int(row["jumlah"]))
            harga = int(row["harga_satuan"])
            bruto = jumlah * harga

            diskon = transform_diskon_rupiah(
                row.get("diskon_persen", "0"), bruto
            )
            neto = bruto - diskon

            if diskon < 0 or diskon > bruto:
                raise ValueError("Diskon di luar rentang nilai transaksi")

            upsert_firestore(
                "fakta_penjualan", row["id_pesanan_nk"], {
                    "sk_waktu": sk_waktu,
                    "sk_produk": sk_produk,
                    "sk_pelanggan": sk_pelanggan,
                    "sk_kurir": kurir["sk"],
                    "sk_metode_bayar": bayar["sk"],
                    "id_pesanan_nk": row["id_pesanan_nk"],
                    "jumlah": jumlah,
                    "harga_satuan": harga,
                    "diskon": diskon,
                    "total_harga_bruto": bruto,
                    "total_penjualan_neto": neto,
                    "ongkos_kirim": int(row["ongkos_kirim"])
                }
            )

            print(
                f"[TRANSFORM OK] {row['id_pesanan_nk']} | "
                f"{row['nama_pelanggan'].title()} | "
                f"Bruto Rp{bruto:,} | Diskon Rp{diskon:,} | "
                f"Neto Rp{neto:,}"
            )

        except (KeyError, ValueError, requests.RequestException) as error:
            print(
                f"[TRANSFORM GAGAL] "
                f"{row.get('id_pesanan_nk', 'Tanpa ID')}: {error}"
            )

    print("\nProses transformasi selesai.")


if __name__ == "__main__":
    extract_and_load_to_landing_zone()
    transform_landing_to_star_schema()
