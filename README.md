<p align="center">
  <img src="assets/cherryBlossomBottom.png" alt="Pink cherry blossom tree" width="420">
</p>

<h1 align="center">🌸 iErase 🌸</h1>

<p align="center">
  A cute and simple desktop app that removes backgrounds from pictures and GIFs.
</p>

<p align="center">
  Choose the quick <strong>Pillow</strong> mode for simple backgrounds, or use
  <strong>AI</strong> mode when the background is more complicated.
</p>

---

## 🌷 About

iErase is a small team project made to make background removal feel easy and friendly.
Upload a picture or GIF, remove its background, preview the result, and save it.

## ✨ What can iErase do?

- Remove backgrounds from GIFs, PNGs, JPGs, and JPEGs
- Process animated GIFs one frame at a time
- Use Pillow for simple backgrounds or AI for complex ones
- Preview the transparent result inside the app
- Download the finished picture or GIF

## 🌸 The app

<p align="center">
  <img src="assets/Image%20of%20the%20main%20app%20.png" alt="The iErase main screen" width="800">
</p>

## 🌱 How to run it

Open PowerShell inside the project folder, then create the virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project packages:

```powershell
python -m pip install -r requirements.txt
```

Start iErase:

```powershell
python main.py
```

> The AI model may take a little longer the first time it runs. 🌱

### 🎁 Build the Windows app

Install the build package:

```powershell
python -m pip install -r requirements-dev.txt
```

Build iErase:

```powershell
.\build_exe.ps1
```

Open `release\iErase\iErase.exe` when the build finishes. Keep the whole
`release\iErase` folder together when you share the app. The AI model is
included, so the finished app can remove backgrounds without downloading it.

## 💗 How to use

1. Pick **Pillow** or **AI** mode.
2. Upload or drag in your picture or GIF.
3. Press **Remove Background**.
4. Preview the transparent result.
5. Press **Download** to save it.

## 🎀 Result

<p align="center">
  <img src="assets/Image%20of%20the%20results%20using%20the%20apop%20.png" alt="A transparent GIF result shown in iErase" width="800">
</p>

## 🌼 What we learned

We learned how to work together with Git branches, process animated GIF frames,
connect background-removal code to a desktop interface, and turn an idea into a working app.

<p align="center">
  Made with Python, Pillow, rembg, PySide6, and lots of pink petals. 🌸
</p>
