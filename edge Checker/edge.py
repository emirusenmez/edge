import requests
from flask import Flask, render_template, request
from concurrent.futures import ThreadPoolExecutor
import csv

app = Flask(__name__)

class URLTester:
    def __init__(self, url):
        self.url = url

    def fetch_ips(self):
        # API'den IP listesi çekiyoruz
        api_url = "https://api.merlincdn.com/ip-list"
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # API isteği başarısız olursa exception fırlatır
            ip_data = response.json()
            return ip_data.get("data", [])
        except requests.RequestException as e:
            print(f"Error fetching IP list: {e}")
            return []

    def test_ip_async(self, ip):
        try:
            # URL'ye istek atıyoruz ve durum kodunu alıyoruz
            response = requests.get(self.url, timeout=5, allow_redirects=False)
            if response.status_code == 301:
                return {"ip": ip, "status_code": "301"}
            else:
                return {"ip": ip, "status_code": response.status_code}
        except requests.exceptions.Timeout as e:
            return {"ip": ip, "status_code": "Timeout", "error": str(e)}
        except requests.RequestException as e:
            return {"ip": ip, "status_code": "Error", "error": str(e)}

    def test_ips(self):
        ips = self.fetch_ips()
        results = []

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.test_ip_async, item.get("ipv4")) for item in ips]
            for future in futures:
                results.append(future.result())

        return results

    def save_results_to_csv(self, results):
        with open('test_results.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            for result in results:
                writer.writerow([result['ip'], result['status_code']])

@app.route("/edgechecker", methods=["GET", "POST"])
def edge_checker():
    results = []
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            tester = URLTester(url)
            results = tester.test_ips()
            tester.save_results_to_csv(results)  # Sonuçları CSV'ye kaydet

    return render_template("edgechecker.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)
