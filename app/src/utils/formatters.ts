export const formatCPF = (value: string) => {
  const digits = value.replace(/\D/g, '').slice(0, 11);
  let formatted = digits;
  if (digits.length > 3) formatted = `${digits.slice(0, 3)}.${digits.slice(3)}`;
  if (digits.length > 6) formatted = `${formatted.slice(0, 7)}.${digits.slice(6)}`;
  if (digits.length > 9) formatted = `${formatted.slice(0, 11)}-${digits.slice(9)}`;
  return formatted;
};

export const formatDate = (value: string) => {
  const digits = value.replace(/\D/g, '').slice(0, 8);
  let formatted = digits;
  if (digits.length > 2) formatted = `${digits.slice(0, 2)}/${digits.slice(2)}`;
  if (digits.length > 4) formatted = `${formatted.slice(0, 5)}/${digits.slice(4)}`;
  return formatted;
};
