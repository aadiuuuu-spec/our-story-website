
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

    // Wait until the page is loaded, then reveal it
    const hideLoader = () => {
        setTimeout(() => {
            loader.classList.add("hide");
        }, 700);
    };

    if (document.readyState === "complete") {
        hideLoader();
    } else {
        window.addEventListener("load", hideLoader, { once: true });
    }

    // Safety fallback
    setTimeout(hideLoader, 12000);
});
