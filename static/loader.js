
document.addEventListener("DOMContentLoaded", () => {
    const loader = document.getElementById("story-loader");

    if (!loader) return;

    // Floating rose petals
    const symbols = ["🌹", "♡", "✦", "🌸"];

    for (let i = 0; i < 22; i++) {
        const petal = document.createElement("span");
        petal.className = "rose-petal";
        petal.textContent = symbols[Math.floor(Math.random() * symbols.length)];

        petal.style.left = Math.random() * 100 + "%";
        petal.style.animationDuration = (6 + Math.random() * 8) + "s";
        petal.style.animationDelay = (Math.random() * 6) + "s";
        petal.style.fontSize = (12 + Math.random() * 16) + "px";

        loader.appendChild(petal);
    }

    // Reveal promptly; remote fonts or slow third-party assets must not
    // leave a blank or frozen-looking screen.
    const hideLoader = () => {
        if (loader.dataset.hiding) return;
        loader.dataset.hiding = "1";
        setTimeout(() => loader.classList.add("hide"), 650);
    };

    requestAnimationFrame(hideLoader);
    setTimeout(hideLoader, 3500);
});
