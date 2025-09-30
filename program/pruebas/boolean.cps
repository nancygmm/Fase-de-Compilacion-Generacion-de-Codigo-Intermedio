function toString(x: integer): string { return ""; }

function decide(a: integer, b: integer, flag: integer): integer {
  if (a > b) {
    if (flag != 0) {
      return 1;
    }
  }

  if (a == b) {
    if (flag == 0) {
      return 1;
    }
  }

  if (a <= b) {
    if (a != 0) {
      if (b < 0) {
      } else {
        return 2;
      }
    }
  }

  return 0;
}

let log: string = "";
let r1: integer = decide(5, 3, 1);
let r2: integer = decide(2, 2, 0);
let r3: integer = decide(0, -1, 0);
log = log + "r1=" + toString(r1) + ", r2=" + toString(r2) + ", r3=" + toString(r3) + "\n";
