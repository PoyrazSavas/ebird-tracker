import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from ebird_client import EBirdClient

# Çıktıları renklendirmek için Rich console
console = Console()

def setup_client():
    """API istemcisini hazırlar."""
    load_dotenv()
    api_key = os.getenv("EBIRD_API_KEY")
    
    if not api_key or api_key == "your_api_key_here":
        console.print("[bold red]Hata:[/bold red] EBIRD_API_KEY bulunamadı!")
        console.print("Lütfen .env dosyasını oluşturun ve geçerli bir eBird API anahtarı ekleyin.")
        sys.exit(1)
        
    return EBirdClient(api_key)

def display_results(obs_list, species_name, hotspot_name):
    """Gözlem sonuçlarını tablo halinde yazdırır."""
    if not obs_list:
        console.print(Panel(
            f"[yellow]{species_name}[/yellow], [bold]{hotspot_name}[/bold] konumunda son 30 gün içinde görülmemiş.",
            title="Sonuç",
            border_style="yellow"
        ))
        return

    table = Table(title=f"\n[bold cyan]{species_name}[/bold cyan] - {hotspot_name} Son Gözlemleri", title_justify="left")
    
    table.add_column("Tarih ve Saat", style="magenta")
    table.add_column("Gözlemci", style="green")
    table.add_column("Sayı", justify="right", style="blue")
    table.add_column("Checklist Bağlantısı", style="underline cyan")

    # En güncel 3 kaydı al
    top_3 = obs_list[:3]

    for obs in top_3:
        # Tarih formatlama (eBird formatı: "2023-10-27 08:30")
        obs_dt = obs.get("obsDt", "Bilinmiyor")
        observer = obs.get("userDisplayName", "Gizli Gözlemci")
        how_many = str(obs.get("howMany", "X"))
        sub_id = obs.get("subId")
        checklist_url = f"https://ebird.org/checklist/{sub_id}"
        
        table.add_row(obs_dt, observer, how_many, checklist_url)

    console.print(table)
    console.print(f"\n[dim]Toplam {len(obs_list)} kayıt bulundu. En güncel 3 kayıt gösteriliyor.[/dim]")

def main():
    console.print(Panel.fit(
        "[bold green]eBird Hotspot Gözlem Sorgulayıcı[/bold green]\n"
        "[dim]Belirli bir türün hotspot üzerindeki son durumunu öğrenin.[/dim]",
        border_style="green"
    ))

    client = setup_client()

    while True:
        try:
            # Kullanıcı girdileri
            hotspot_id = Prompt.ask("[bold blue]Hotspot ID girin[/bold blue] (örn. L123456)")
            species_query = Prompt.ask("[bold blue]Kuş Türü Adı veya Kodu girin[/bold blue]")

            with console.status("[bold green]Veriler çekiliyor...") as status:
                # Tür kodunu bul
                species_code = client.get_species_code(species_query)
                if not species_code:
                    console.print(f"[red]Hata:[/red] '{species_query}' türü bulunamadı. Lütfen İngilizce isim veya eBird kodu deneyin.")
                    continue

                # Hotspot adını al (doğrulama için)
                hotspot_name = client.get_hotspot_name(hotspot_id)
                
                # Gözlemleri çek
                observations = client.get_hotspot_observations(hotspot_id, species_code)
                
                # Sonuçları göster
                display_results(observations, species_query.title(), hotspot_name)

            # Devam etmek istiyor mu?
            if not Prompt.ask("\nYeni bir sorgu yapmak ister misiniz?", choices=["evet", "hayır"], default="evet") == "evet":
                break
                
        except Exception as e:
            console.print(f"[bold red]Hata:[/bold red] {str(e)}")
            if not Prompt.ask("\nTekrar denemek ister misiniz?", choices=["evet", "hayır"], default="evet") == "evet":
                break

    console.print("[bold green]Güle güle! İyi gözlemler.[/bold green]")

if __name__ == "__main__":
    main()
