"""
Script automático para subir ORION Mobile a GitHub
"""
import os
import subprocess
import webbrowser

def run_command(command, description):
    """Ejecuta comando y muestra resultado"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Completado")
            return True
        else:
            print(f"❌ {description} - Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def setup_github_repo():
    """Configura y sube a GitHub"""
    
    print("🚀 ORION Mobile - Setup Automático GitHub")
    print("=" * 50)
    
    # Pedir información del usuario
    github_username = input("\n👤 Tu usuario de GitHub: ").strip()
    repo_name = input("📁 Nombre del repositorio (ej: orion-mobile): ").strip() or "orion-mobile"
    git_email = input("📧 Tu email para Git: ").strip()
    git_name = input("👤 Tu nombre para Git: ").strip()
    
    if not github_username:
        print("❌ El usuario de GitHub es obligatorio")
        return
    
    # Configurar identidad Git
    print("\n🔧 Configurando identidad Git...")
    run_command(f'git config user.email "{git_email}"', "Configurando email")
    run_command(f'git config user.name "{git_name}"', "Configurando nombre")
    
    repo_url = f"https://github.com/{github_username}/{repo_name}.git"
    
    print(f"\n🎯 Configurando repositorio: {repo_url}")
    
    # Comandos Git
    commands = [
        ("git init", "Inicializando Git"),
        ("git add .", "Añadiendo archivos"),
        ("git commit -m \"ORION Mobile - Version inicial\"", "Creando commit"),
        (f"git remote add origin {repo_url}", "Conectando con GitHub"),
        ("git branch -M main", "Configurando rama main"),
        ("git push -u origin main", "Subiendo a GitHub")
    ]
    
    # Ejecutar comandos
    for command, description in commands:
        if not run_command(command, description):
            print(f"\n⚠️ Error en: {description}")
            print("📋 Revisa el error y vuelve a intentarlo")
            return
    
    print("\n" + "=" * 50)
    print("🎉 ¡ÉXITO! ORION Mobile subido a GitHub")
    print(f"🌐 Repositorio: {repo_url}")
    print("\n📱 Siguientes pasos:")
    print("1. Ve a tu repositorio en GitHub")
    print("2. Espera 5-10 minutos la compilación")
    print("3. Descarga la APK desde Actions")
    print("4. ¡Instala en tu Android!")
    
    # Abrir repositorio
    try:
        webbrowser.open(repo_url)
        print(f"\n🌐 Abriendo repositorio en navegador...")
    except:
        print(f"\n📂 Abre manualmente: {repo_url}")

if __name__ == "__main__":
    setup_github_repo()
