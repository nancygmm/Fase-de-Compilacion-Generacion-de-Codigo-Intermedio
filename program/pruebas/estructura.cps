function toString(x: integer): string { return ""; }

let log: string = "";

function esPar(n: integer): boolean { return (n - (n / 2) * 2) == 0; }

function mainCompute(n: integer): integer {
  let acc: integer = 0;

  if (n > 5) { acc = acc + 1; }
  else { acc = acc - 1; }

  let i: integer = 0;
  while (i < n) {
    if (esPar(i)) { acc = acc + 2; }
    else { acc = acc - 1; }
    i = i + 1;
  }
  return acc;
}

let r: integer = mainCompute(6);
log = log + "acc=" + toString(r) + "\n";
