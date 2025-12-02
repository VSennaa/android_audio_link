# AudioDroid (GUI)

Interface minimalista para conectar `scrcpy` apenas para áudio (playback), com fallbacks (quick connect, set 5555 via USB, manual connect), persistência de configurações (`config.json`) e controle visual de conexão.

---

## 🚀 Como usar

### 1. Pré-requisitos e Instalação do Scrcpy
O AudioDroid requer os binários do scrcpy para funcionar.

1.  **Baixe o scrcpy v3.3.2**:
    Acesse o site oficial e baixe a versão **3.3.2**:
    [https://github.com/Genymobile/scrcpy/releases/tag/v3.3.2](https://github.com/Genymobile/scrcpy/releases/tag/v3.3.2)
2.  **Extração**:
    Extraia a pasta do scrcpy em um local seguro do seu computador.
    *Exemplo:* `D:\scrcpy-win64-v3.3.2`

### 2. Executando o AudioDroid
1.  Execute o arquivo **`scycrp_aud_gui.exe`**.
2.  **Primeira Execução**: O programa pedirá para selecionar a **pasta raiz** onde você extraiu o scrcpy.
    * O sistema valida automaticamente a existência de `scrcpy.exe` e `adb.exe`.
3.  Um arquivo `config.json` será gerado para salvar o caminho e suas preferências de IP/Porta.

### 3. Interface e Controles

#### Campos
* **IP:** Endereço do dispositivo Android (Ex: `10.0.0.100`).
* **Porta:** Porta ADB (Padrão: `5555`).
* **Buffer:** Latência de áudio em ms (Padrão: `200`).

#### Ações
* **Conexão Rápida:** Tenta conectar no IP/Porta definidos e abre o áudio imediatamente.
* **Parear:** Inicia o pareamento ADB (Wireless).
  > ⚠️ **Atenção:** O pareamento via interface ainda não está totalmente concluído. Caso falhe, realize o processo manualmente via terminal (CMD/Powershell) na pasta do scrcpy:
  > ```bash
  > adb pair HOST[:PORT] [PAIRING CODE]
  > ```
* **Conexão Manual:** Permite forçar conexão em IP específico.
* **Fechar Conexão:** Desconecta o ADB e encerra o processo do scrcpy, mantendo a janela aberta.

#### Observações
* **Logs:** O status da conexão e erros aparecem no painel inferior da janela.
* **Encerramento:** Ao fechar a janela, o scrcpy é finalizado e a conexão ADB é encerrada automaticamente para economizar bateria do dispositivo.

> **Nota:** Ferramenta testada e validada no **Windows** com **scrcpy 3.3.2**.

---

## 🛠️ Desenvolvimento e Build

Caso queira rodar o código fonte ou compilar por conta própria.

### Requisitos
* Windows 10/11 (Adaptável para Linux/macOS)
* Python 3.8+
* `scrcpy` e `adb` acessíveis (no PATH ou apontados na config)

### Instalação do Ambiente

```bash
# Criação do ambiente virtual
python -m venv .venv

# Ativação
.venv\Scripts\activate

# Instalação das dependências
pip install --upgrade pip
pip install customtkinter
