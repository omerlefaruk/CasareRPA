<rules category="ui">
  <signals id="qt-signals" priority="normal">
    <name>Qt Signal/Slot Rules</name>

    <constraint>
      <rule>@Slot decorator REQUIRED for all signal handlers</rule>
      <forbidden>NO lambdas as signal handlers</forbidden>
      <reason>Lambdas cause garbage collection issues</reason>
    </constraint>

    <correct>
      <code><![CDATA[
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        button.clicked.connect(self.on_click)

    @Slot()
    def on_click(self):
        # Handle click
        pass
]]></code>
    </correct>

    <wrong>
      <code><![CDATA[
# WRONG: Lambda will be garbage collected
button.clicked.connect(lambda: self.do_something())

# WRONG: No @Slot decorator
def on_click(self):
    pass
button.clicked.connect(self.on_click)
]]></code>
    </wrong>

    <async_integration>
      <rule>Qt integration via qasync</rule>
      <file>@src/casare_rpa/infrastructure/async_utils.py</file>
    </async_integration>

    <references>
      <ref>@.claude/rules/ui/signal-slot-rules.md</ref>
      <ref>@docs/agent/ui-signal-slot.md</ref>
    </references>
  </signals>
</rules>
