
/* OUR STORY — FIXED CINEMATIC EFFECTS */
(() => {
    "use strict";

    const title = document.getElementById("chapterTitle");
    const body = document.getElementById("chapterText");

    if (!title || !body) {
        console.error("OUR STORY: Chapter elements not found.");
        return;
    }

    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    let lastChapter = "";
    let typingTimer = null;
    let secretTaps = 0;
    let secretTimer = null;

    const wait = ms =>
        new Promise(resolve => setTimeout(resolve, ms));

    function addKicker() {
        document.querySelector(".os-kicker")?.remove();

        const kicker = document.createElement("div");
        kicker.className = "os-kicker";
        kicker.textContent = "A LITTLE UNIVERSE, MADE FOR TWO";

        title.parentNode.insertBefore(kicker, title);
    }

    function typeText() {
        clearInterval(typingTimer);

        if (reducedMotion) return;

        const originalText = body.textContent || "";

        if (originalText.length < 45 ||
            originalText.length > 1600) return;

        body.textContent = "";

        const cursor = document.createElement("span");
        cursor.textContent = "▍";
        body.appendChild(cursor);

        let position = 0;

        typingTimer = setInterval(() => {
            if (!cursor.isConnected) {
                clearInterval(typingTimer);
                return;
            }

            cursor.insertAdjacentText(
                "beforebegin",
                originalText.slice(position, position + 2)
            );

            position += 2;

            if (position >= originalText.length) {
                clearInterval(typingTimer);
                cursor.remove();
            }
        }, 22);
    }

    async function heartScan() {
        document.querySelector(".os-scan")?.remove();

        const scan = document.createElement("div");
        scan.className = "os-scan";

        scan.innerHTML = `
            <div>♡ HEART DATABASE // PRIVATE ARCHIVE</div>

            <div class="bar">
                <div class="fill"></div>
            </div>

            <span class="status">
                Initializing heart connection...
            </span>

            <span class="percent">0%</span>
        `;

        body.insertAdjacentElement("afterend", scan);

        const fill = scan.querySelector(".fill");
        const status = scan.querySelector(".status");
        const percent = scan.querySelector(".percent");

        const steps = [
            [7, "Gathering little moments..."],
            [18, "Remembering shared smiles..."],
            [32, "Saving the sweetest memories..."],
            [46, "Keeping every promise close..."],
            [61, "Celebrating the story so far..."],
            [78, "A thousand reasons, one feeling..."],
            [92, "The answer has always been clear..."],
            [100, "YOU ARE MY FAVOURITE PERSON ✨"]
        ];

        for (const [value, message] of steps) {
            if (!scan.isConnected) return;

            fill.style.width = value + "%";
            percent.textContent = value + "%";
            status.textContent = message;

            await wait(reducedMotion ? 0 : 450);
        }

        status.textContent =
            "A LITTLE FOREVER — written with love. ❤️";
    }

    function updateChapter() {
        const heading = title.textContent.trim();
        const chapterText = body.textContent.trim();

        const key = heading + "|" + chapterText;

        if (!heading || key === lastChapter) return;

        lastChapter = key;

        addKicker();

        title.classList.remove("os-enter");
        body.classList.remove("os-enter");

        void title.offsetWidth;

        title.classList.add("os-enter");
        body.classList.add("os-enter");

        document.querySelector(".os-scan")?.remove();

        const searchText =
            (heading + " " + chapterText).toLowerCase();

        if (
            searchText.includes("heart database")
        ) {
            heartScan();
        } else {
            typeText();
        }
    }

    /*
       IMPORTANT:
       Observe the heading only.
       This prevents the typewriter effect from restarting itself.
    */

    const observer = new MutationObserver(updateChapter);

    observer.observe(title, {
        childList: true,
        subtree: true,
        characterData: true
    });

    updateChapter();

    // Floating hearts on button clicks
    document.addEventListener("click", event => {
        const target = event.target.closest(
            "button, a, #chapterNav, #openStory"
        );

        if (!target) return;

        for (let i = 0; i < 5; i++) {
            const heart = document.createElement("span");

            heart.className = "os-heart-burst";
            heart.textContent = ["♡", "♥", "✦"][i % 3];

            heart.style.left = event.clientX + "px";
            heart.style.top = event.clientY + "px";

            heart.style.setProperty(
                "--dx",
                (Math.random() - 0.5) * 110 + "px"
            );

            heart.style.setProperty(
                "--dy",
                -30 - Math.random() * 90 + "px"
            );

            document.body.appendChild(heart);

            setTimeout(() => heart.remove(), 1200);
        }
    });

    // Hidden romantic message: tap chapter title 7 times
    title.addEventListener("click", () => {
        secretTaps++;

        clearTimeout(secretTimer);

        secretTimer = setTimeout(() => {
            secretTaps = 0;
        }, 1800);

        if (secretTaps < 7) return;

        secretTaps = 0;

        const secret = document.createElement("div");
        secret.className = "os-secret";

        secret.innerHTML = `
            <div class="os-secret-card">
                <div>✦ SECRET MEMORY UNLOCKED ✦</div>

                <h2>Only You. ❤️</h2>

                <p>
                    Out of all the moments this world could
                    have given me, I would still choose the
                    ones that led me to you. ♡
                </p>

                <button type="button">
                    Keep this secret
                </button>
            </div>
        `;

        secret.addEventListener("click", event => {
            if (
                event.target === secret ||
                event.target.tagName === "BUTTON"
            ) {
                secret.remove();
            }
        });

        document.body.appendChild(secret);
    });

    console.log("OUR STORY cinematic effects loaded ❤️");

})();
                                  
