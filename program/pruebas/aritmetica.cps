function toString(x: integer): string { return ""; }

function mix(a: integer, b: integer, c: integer): integer {
  let t1: integer = a + b * c;
  let t2: integer = (a + b) * c;
  let t3: integer = a - b - c;
  let t4: integer = a * (b - c) + 10 / 2;
  return t1 + t2 + t3 + t4;
}

let log: string = "";
let m: integer = mix(6, 4, 2);
log = log + "mix=" + toString(m) + "\n";
