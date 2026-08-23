Output assets/demo.gif
Set FontSize 15
Set Width 1200
Set Height 640
Set Padding 20
Set Theme Dracula

Show

Type "wenti list"
Sleep 1200ms
Enter
Sleep 2500ms

Type "printf '%s' '随着人工智能的快速发展，越来越多的创作者开始使用 AI 工具辅助写作。首先，AI 可以提升效率。其次，AI 能够降低门槛。最后，AI 有助于拓宽表达边界。综上所述，AI 写作是大势所趋。因此，我们应该积极拥抱这一变化。' > /tmp/wenti_demo.md"
Sleep 800ms
Enter
Sleep 1200ms

Type "wenti score /tmp/wenti_demo.md --pack sanlian --dry-run"
Sleep 1200ms
Enter
Sleep 5000ms

Type "wenti score /tmp/wenti_demo.md --pack sanlian --dry-run --json"
Sleep 1200ms
Enter
Sleep 3500ms
