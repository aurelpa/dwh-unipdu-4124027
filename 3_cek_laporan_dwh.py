
import requests
import pandas as pd

MY_PROJECT_ID = "dwh-unipdu-4124027"


def fetch_collection_as_df(collection_name):
    url = (
        "https://firestore.googleapis.com/v1/projects/"
        f"{MY_PROJECT_ID}/databases/(default)/documents/"
        f"{collection_name}"
    )

    rows = []
    page_token = None

    while True:
        params = {"pageSize": 1000}
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        result = response.json()

        for doc in result.get("documents", []):
            item = {}

            for key, value in doc.get("fields", {}).items():
                if "integerValue" in value:
                    item[key] = int(value["integerValue"])
                elif "doubleValue" in value:
                    item[key] = float(value["doubleValue"])
                elif "stringValue" in value:
                    item[key] = value["stringValue"]

            rows.append(item)

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Tabel 1: Data mentah
    df_raw = fetch_collection_as_df("landing_zone_raw")

    kolom_raw = [
        "id_pesanan_nk",
        "sumber_project",
        "nama_pelanggan",
        "jenis_kelamin",
        "nama_provinsi",
        "jumlah",
        "diskon_persen"
    ]

    print("\n=== 1. DATA MENTAH DI LANDING ZONE ===")

    if df_raw.empty:
        print("Belum ada data. Jalankan seeder dan pipeline terlebih dahulu.")
    else:
        tersedia = [c for c in kolom_raw if c in df_raw.columns]
        print(df_raw[tersedia].to_markdown(index=False))

    # Tabel 2: Hasil JOIN skema bintang
    df_fakta = fetch_collection_as_df("fakta_penjualan")
    df_waktu = fetch_collection_as_df("dim_waktu")
    df_produk = fetch_collection_as_df("dim_produk")
    df_pelanggan = fetch_collection_as_df("dim_pelanggan")
    df_kurir = fetch_collection_as_df("dim_kurir")
    df_bayar = fetch_collection_as_df("dim_metode_bayar")

    print("\n=== 2. HASIL JOIN SKEMA BINTANG DWH ===")

    data_dimensi = [
        df_fakta, df_waktu, df_produk,
        df_pelanggan, df_kurir, df_bayar
    ]

    if any(df.empty for df in data_dimensi):
        print("Data fakta atau dimensi belum lengkap.")
        print("Periksa hasil pipeline ELT terlebih dahulu.")
    else:
        df_join = (
            df_fakta
            .merge(df_waktu, on="sk_waktu")
            .merge(df_produk, on="sk_produk")
            .merge(df_pelanggan, on="sk_pelanggan")
            .merge(df_kurir, on="sk_kurir")
            .merge(df_bayar, on="sk_metode_bayar")
        )

        kolom_dwh = [
            "id_pesanan_nk",
            "tanggal_penjualan",
            "kuartal",
            "nama_pelanggan",
            "jenis_kelamin",
            "kelompok_usia",
            "nama_provinsi",
            "pulau",
            "nama_produk",
            "jumlah",
            "total_harga_bruto",
            "diskon",
            "total_penjualan_neto"
        ]

        tersedia = [c for c in kolom_dwh if c in df_join.columns]
        print(df_join[tersedia].to_markdown(index=False))
