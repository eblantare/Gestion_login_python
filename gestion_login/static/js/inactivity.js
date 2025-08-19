let inactivityTime = function () {
    let time;
    let countdown;
    const warningTime = 5 * 60 * 1000; // 5 minutes
    const logoutTime = 30; // 30 seconds countdown

    function resetTimer() {
        clearTimeout(time);
        clearInterval(countdown);
        time = setTimeout(showWarning, warningTime);
    }

    function showWarning() {
        let remaining = logoutTime;
        document.getElementById('countdown').textContent = remaining;
        let modal = new bootstrap.Modal(document.getElementById('inactivityModal'));
        modal.show();

        countdown = setInterval(() => {
            remaining--;
            document.getElementById('countdown').textContent = remaining;
            if (remaining <= 0) {
                clearInterval(countdown);
                window.location.href = '/login';
            }
        }, 1000);
    }

    window.onload = resetTimer;
    document.onmousemove = resetTimer;
    document.onkeydown = resetTimer;
};

inactivityTime();