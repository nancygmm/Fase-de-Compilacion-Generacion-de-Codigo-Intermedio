from CompiscriptVisitor import CompiscriptVisitor
from managers import TempManager, LabelManager

class IRGenerator(CompiscriptVisitor):
    def __init__(self, symbol_table):
        self.temp_manager = TempManager()
        self.label_manager = LabelManager()
        self.symbol_table = symbol_table
        self.code = []

    def visitAssignment(self, ctx):
        expr = self.visit(ctx.expression())
        var_name = ctx.Identifier().getText()
        self.code += expr["code"]
        self.code.append(("=", expr["place"], None, var_name))
        return {"code": self.code, "place": var_name}

    def visitAdditiveExpr(self, ctx):
        if len(ctx.multiplicativeExpr()) == 1:
            return self.visit(ctx.multiplicativeExpr(0))
        left = self.visit(ctx.multiplicativeExpr(0))
        right = self.visit(ctx.multiplicativeExpr(1))
        temp = self.temp_manager.new_temp()
        code = left["code"] + right["code"]
        code.append(("+", left["place"], right["place"], temp))
        return {"code": code, "place": temp}
