const passwordInput = document.getElementById('id_password');
const passwordToggle = document.querySelector('.password-toggle');

if (passwordInput && passwordToggle) {
    passwordToggle.hidden = false;
    passwordToggle.addEventListener('click', () => {
        const showPassword = passwordInput.type === 'password';
        passwordInput.type = showPassword ? 'text' : 'password';
        passwordToggle.textContent = showPassword ? 'Hide password' : 'Show password';
        passwordToggle.setAttribute('aria-pressed', String(showPassword));
    });
}
