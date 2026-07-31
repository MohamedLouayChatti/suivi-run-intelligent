const PASSWORD_REQUIREMENTS_TEXT =
  "Minimum 10 caractères, avec une majuscule, une minuscule, un chiffre et un symbole.";

const PASSWORD_PATTERN = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{10,}$/;

function isPasswordValid(password: string): boolean {
  return PASSWORD_PATTERN.test(password);
}

export { PASSWORD_REQUIREMENTS_TEXT, isPasswordValid };
