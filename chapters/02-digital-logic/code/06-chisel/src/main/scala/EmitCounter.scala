import circt.stage.ChiselStage

object EmitCounter extends App {
  ChiselStage.emitSystemVerilogFile(
    new EnabledCounter(4),
    args = args
  )
}
