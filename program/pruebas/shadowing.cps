function toString(x: integer): string { return ""; }

let g: integer = 3;

class Box {
  let g: integer;

  function constructor(v: integer) { this.g = v; }

  function demo(): integer {
    let g: integer = 7;
    return g + this.g; 
  }
}

let log: string = "";

let b: Box = new Box(5);
let r1: integer = b.demo(); 
let r2: integer = g;        
log = log + "suma=" + toString(r1 + r2) + "\n";
