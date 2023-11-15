document.addEventListener("DOMContentLoaded", function () {
    const symbols = ["🍒", "🍋", "🍇", "🍊", "🍉"];
    const reels = [
        document.getElementById("reel1"),
        document.getElementById("reel2"),
        document.getElementById("reel3")];
    const creditValue = document.getElementById("credit_value");
    const spinButton = document.getElementById("spin-button");
    spinButton.disabled = true;
    const init_symbols = [...symbols];
    
    for (let i = 0; i < reels.length; i++) { // init random fuits
        const chosen_element = Math.floor(Math.random() * init_symbols.length);
        const randomSymbol = init_symbols[chosen_element];
        reels[i].textContent = randomSymbol;
        init_symbols.splice(chosen_element, 1);
    }

    fetch('/new_user.json')
    .then(response => response.json())
    .then(user_info => spinHandler(user_info))
    .catch(error => console.error('Error:', error));

    function spinHandler(user_info) {
        console.log(user_info);
        const credit = user_info['credit'];
        creditValue.innerText = credit;
        if (credit>0) spinButton.disabled = false;
        const user_id = user_info['user_id'];
        spinButton.addEventListener("click", () => {
            spinButton.disabled = true;
            console.log('spin by user_id:' + user_id);
            spinToWin(user_id);
        });
    }

    function spinToWin(user_id){
        fetch('/spin/'+user_id+'.json')
        .then(response => response.json())
        .then(user_info => spinReels(user_info))
        .catch(error => console.error('Error:', error));
    }

    function spinReels(user_info) {
        console.log(user_info);
        let spinsLeft = 10;
        const spinInterval = setInterval(() => {
            for (let i = 0; i < reels.length; i++) {
                const randomSymbol = symbols[Math.floor(Math.random() * symbols.length)];
                reels[i].textContent = randomSymbol;
            }
            spinsLeft--;
            if (spinsLeft === 0) {
                clearInterval(spinInterval);
                const spin_symbols = [...symbols];
                if (!user_info['win']) {
                    for (let i = 0; i < reels.length; i++) { // spin random fuits
                        const chosen_element = Math.floor(Math.random() * spin_symbols.length)
                        const randomSymbol = spin_symbols[chosen_element];
                        reels[i].textContent = randomSymbol;
                        spin_symbols.splice(chosen_element, 1);
                    }
                } else {
                    const chosen_element = Math.floor(Math.random() * spin_symbols.length);
                    for (let i = 0; i < reels.length; i++) {
                        const randomSymbol = spin_symbols[chosen_element];
                        reels[i].textContent = randomSymbol;
                    }
                    confetti({
                        particleCount: 100,
                        spread: 70,
                        origin: { y: 0.6 }
                    });
                }
                const credit = user_info['credit'];
                creditValue.innerText = credit;
                if (credit>0) spinButton.disabled = false;
            }
        }, 100);
    }
});