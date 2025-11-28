<context>
  <meta>
    <rules>
      1. Be EXTREMELY concise. Sacrifice grammar.
      2. NO estimated effort/time/complexity ratings.
    </rules>
    <cmds>
      <run>python run.py</run>
      <install>pip install -e .</install>
      <test>pytest tests/ -v</test>
    </cmds>
  </meta>

  <project name="CasareRPA">
    <overview>
      Windows Desktop RPA platform with visual node-based workflow editor.
      Enables Web (Playwright) and Desktop (UIAutomation) automation via drag-and-drop.
      Follows Clean Architecture (DDD).
    </overview>

    <stack>
      Python 3.12+, PySide6 (GUI), NodeGraphQt, Playwright, uiautomation,
      qasync (Qt+Asyncio), orjson, loguru, APScheduler, asyncpg/aiomysql.
    </stack>

    <architecture style="Clean DDD">
      <flow>Presentation → Application → Domain ← Infrastructure</flow>
      <layers>
        <layer name="Domain">Pure logic. Entities, VO, Services. NO deps.</layer>
        <layer name="Application">Use Cases. Coordinates Domain + Infra.</layer>
        <layer name="Infrastructure">Impl Domain interfaces. Resources, Persistence, Adapters.</layer>
        <layer name="Presentation">UI. Canvas, Controllers, EventBus. Depends on App.</layer>
      </layers>
      <structure>
        src/casare_rpa/ [domain, application, infrastructure, presentation, nodes, core]
      </structure>
    </architecture>

    <patterns>
      <item>Controller: MainWindow delegates to specialized controllers.</item>
      <item>EventBus: Pub/sub system for loose coupling.</item>
      <item>Async-First: All I/O operations async (Playwright/Qt).</item>
      <item>Trigger System: Registry-based (Manual, Scheduled, Webhook, File, AppEvent, etc).</item>
      <item>Connection Pooling: Browser contexts, DB connections, HTTP sessions.</item>
    </patterns>

    <plans>
      <instruction>At the end of each plan, list unresolved questions to answer. Be extremely concise.</instruction>
      <roadmap>
        Current: Refactoring v2→v3 (Clean Architecture).
        Tasks: Complete trigger system, Project management, Perf optimization, Remove legacy core/ &amp; visual_nodes.
      </roadmap>
    </plans>

    <tdd>
      <philosophy>
        <principle>Test-First for NEW features. Test-After for BUGS (characterization tests).</principle>
        <principle>Domain layer: Pure unit tests, NO mocks.</principle>
        <principle>Application layer: Mock infrastructure, real domain.</principle>
        <principle>Infrastructure: Mock ALL external APIs (Playwright, UIAutomation, win32).</principle>
        <principle>Nodes: Use category fixtures from conftest.py.</principle>
      </philosophy>

      <workflow>
        <cycle name="Red-Green-Refactor">
          <step name="Red">Write failing test. Run: pytest path/to/test.py::test_name -v</step>
          <step name="Green">Write minimal code to pass. Async? Use AsyncMock.</step>
          <step name="Refactor">Clean code. Tests still pass.</step>
          <step name="Commit">git add tests/ src/ &amp;&amp; git commit -m "feat: description"</step>
        </cycle>

        <async_cycle>
          <note>For async code, mark test with @pytest.mark.asyncio</note>
          <example>
            # Red
            @pytest.mark.asyncio
            async def test_execute_workflow_success():
                orchestrator = ExecutionOrchestrator()
                result = await orchestrator.execute(workflow_id)
                assert result.status == ExecutionStatus.COMPLETED

            # Green - implement async execute()
          </example>
        </async_cycle>
      </workflow>

      <layers>
        <domain>
          <rule>NO mocks. Test pure logic with real domain objects.</rule>
          <rule>Value Objects: Test immutability, validation, equality.</rule>
          <rule>Entities: Test behavior, state transitions, invariants.</rule>
          <rule>Services: Test orchestration logic with real VOs/Entities.</rule>

          <example file="tests/domain/test_workflow.py">
            class TestWorkflow:
                def test_add_node_updates_graph(self):
                    workflow = Workflow(name="test", description="")
                    node = Node(id=NodeId("node1"), type="start")

                    workflow.add_node(node)

                    assert len(workflow.nodes) == 1
                    assert workflow.nodes[0].id == NodeId("node1")

                def test_add_duplicate_node_raises_error(self):
                    workflow = Workflow(name="test", description="")
                    node = Node(id=NodeId("node1"), type="start")
                    workflow.add_node(node)

                    with pytest.raises(DuplicateNodeError):
                        workflow.add_node(node)
          </example>
        </domain>

        <application>
          <rule>Mock infrastructure (repos, adapters). Use REAL domain objects.</rule>
          <rule>Test use case orchestration, error handling, transactions.</rule>
          <rule>AsyncMock for async infrastructure dependencies.</rule>

          <example file="tests/application/test_execute_workflow.py">
            @pytest.mark.asyncio
            async def test_execute_workflow_saves_result(mocker):
                # Arrange: Mock infrastructure, real domain
                mock_repo = mocker.AsyncMock(spec=WorkflowRepository)
                mock_repo.get_by_id.return_value = Workflow(name="test")

                orchestrator = ExecutionOrchestrator(repository=mock_repo)

                # Act
                result = await orchestrator.execute(workflow_id=WorkflowId("wf1"))

                # Assert
                assert result.status == ExecutionStatus.COMPLETED
                mock_repo.save_execution.assert_called_once()
          </example>
        </application>

        <infrastructure>
          <rule>Mock ALL external APIs: Playwright, UIAutomation, win32, HTTP, DB.</rule>
          <rule>Use existing fixtures from tests/nodes/*/conftest.py</rule>
          <rule>Create realistic mocks (behavioral, not stubs).</rule>

          <fixtures>
            <global file="tests/conftest.py">execution_context, mock_execution_context</global>
            <browser file="tests/nodes/browser/conftest.py">mock_page, mock_browser, mock_browser_context</browser>
            <desktop file="tests/nodes/desktop/conftest.py">MockUIControl, MockDesktopElement, mock_win32</desktop>
            <http file="tests/nodes/conftest.py">create_mock_response(), create_mock_session()</http>
          </fixtures>

          <example file="tests/nodes/browser/test_browser_nodes.py">
            @pytest.mark.asyncio
            async def test_click_element_success(execution_context, mock_page):
                # Arrange
                node = ClickElementNode(selector="#btn", timeout=5000)
                mock_element = AsyncMock()
                mock_page.query_selector.return_value = mock_element
                execution_context.resources["page"] = mock_page

                # Act
                result = await node.execute(execution_context)

                # Assert
                assert result["success"] is True
                mock_element.click.assert_awaited_once()
          </example>
        </infrastructure>

        <presentation>
          <rule>Use pytest-qt (qtbot fixture) for Qt widgets.</rule>
          <rule>Mock heavy components (NodeGraphQt graph, Canvas).</rule>
          <rule>Test controller logic, NOT Qt internals.</rule>
          <rule>Minimal coverage (qasync + Qt complexity).</rule>

          <example file="tests/presentation/test_workflow_controller.py">
            def test_save_workflow_updates_graph(qtbot, mocker):
                # Arrange
                mock_use_case = mocker.Mock(spec=SaveWorkflowUseCase)
                controller = WorkflowController(save_use_case=mock_use_case)

                # Act
                controller.save_workflow(workflow_data={...})

                # Assert
                mock_use_case.execute.assert_called_once()
          </example>
        </presentation>

        <nodes>
          <rule>Test 3 scenarios: SUCCESS, ERROR, EDGE_CASES.</rule>
          <rule>Use category-specific fixtures (browser, desktop, http).</rule>
          <rule>Verify execution_context updates (variables, resources).</rule>

          <template>
            @pytest.mark.asyncio
            async def test_node_success(execution_context, category_fixtures):
                # Arrange: Configure node + mocks
                node = SomeNode(param1="value")
                # Setup mocks from fixtures

                # Act
                result = await node.execute(execution_context)

                # Assert
                assert result["success"] is True
                assert execution_context.variables["output_var"] == expected_value

            @pytest.mark.asyncio
            async def test_node_error_handling(execution_context, category_fixtures):
                # Arrange: Configure to fail
                node = SomeNode(param1="invalid")
                # Setup mock to raise exception

                # Act
                result = await node.execute(execution_context)

                # Assert
                assert result["success"] is False
                assert "error" in result
          </template>
        </nodes>
      </layers>

      <async_testing>
        <rules>
          <rule>Mark async tests: @pytest.mark.asyncio</rule>
          <rule>Mock async calls: AsyncMock() not Mock()</rule>
          <rule>Assert awaited: mock.assert_awaited_once()</rule>
          <rule>Async context managers: use async with AsyncMock()</rule>
        </rules>

        <decision_tree>
          <question>Is the function async def?</question>
          <yes>
            <step>Use @pytest.mark.asyncio</step>
            <step>Mock with AsyncMock()</step>
            <step>Assert with assert_awaited_*()</step>
          </yes>
          <no>
            <step>Regular def test_*()</step>
            <step>Mock with Mock()</step>
            <step>Assert with assert_called_*()</step>
          </no>
        </decision_tree>

        <examples>
          <async_context_manager>
            # Testing async context manager
            @pytest.mark.asyncio
            async def test_browser_resource_manager():
                mock_browser = AsyncMock()
                manager = BrowserResourceManager()
                manager._browser = mock_browser

                async with manager.get_context() as ctx:
                    assert ctx is not None

                mock_browser.new_context.assert_awaited_once()
          </async_context_manager>

          <mock_vs_asyncmock>
            # WRONG - Mock for async function
            mock_repo = Mock()
            await mock_repo.save()  # Won't work properly

            # RIGHT - AsyncMock for async function
            mock_repo = AsyncMock()
            await mock_repo.save()  # Works correctly
            mock_repo.save.assert_awaited_once()
          </mock_vs_asyncmock>
        </examples>
      </async_testing>

      <mocking_strategy>
        <always_mock>
          <item>Playwright (Page, Browser, BrowserContext)</item>
          <item>UIAutomation (Control, Pattern, Element)</item>
          <item>win32 APIs (win32gui, win32con, ctypes)</item>
          <item>HTTP clients (aiohttp.ClientSession, httpx)</item>
          <item>Database connections (asyncpg, aiomysql)</item>
          <item>File system I/O (aiofiles, pathlib for large files)</item>
          <item>PIL/Image operations</item>
          <item>External processes (subprocess)</item>
        </always_mock>

        <prefer_real>
          <item>Domain entities (Workflow, Node, ExecutionState)</item>
          <item>Value objects (NodeId, PortId, DataType)</item>
          <item>Domain services (pure logic, no I/O)</item>
          <item>Simple data structures (dict, list, dataclasses)</item>
        </prefer_real>

        <context_dependent>
          <item>ExecutionContext - Use fixture from conftest.py</item>
          <item>Event bus - Mock for unit tests, real for integration</item>
          <item>Resource managers - Mock external resources, real manager logic</item>
        </context_dependent>

        <realistic_mocks>
          <principle>Mocks should behave like real objects, not just return values.</principle>

          <example name="MockUIControl">
            # Good: Behavioral mock
            class MockUIControl:
                def __init__(self, name="Button", control_type="Button"):
                    self.Name = name
                    self.ControlType = control_type
                    self._enabled = True

                def GetCurrentPropertyValue(self, property_id):
                    if property_id == 30003:  # IsEnabled
                        return self._enabled
                    raise PropertyNotSupported()

            # Bad: Stub that just returns values
            mock = Mock()
            mock.Name = "Button"  # Doesn't behave like real API
          </example>
        </realistic_mocks>
      </mocking_strategy>

      <test_structure>
        <naming>
          <file>test_&lt;module_name&gt;.py (e.g., test_workflow.py)</file>
          <class>Test&lt;ClassName&gt; (e.g., TestWorkflow, TestExecutionOrchestrator)</class>
          <method>test_&lt;behavior&gt;_&lt;condition&gt;_&lt;expected&gt; (e.g., test_add_node_when_duplicate_raises_error)</method>
        </naming>

        <organization>
          <class_based>
            # Group related tests by SUT (System Under Test)
            class TestWorkflow:
                def test_add_node_success(self): ...
                def test_add_node_duplicate_error(self): ...
                def test_remove_node_success(self): ...

            class TestWorkflowValidation:
                def test_validate_empty_workflow_fails(self): ...
                def test_validate_disconnected_nodes_fails(self): ...
          </class_based>

          <fixture_placement>
            <global>tests/conftest.py - Fixtures used across ALL tests</global>
            <category>tests/&lt;category&gt;/conftest.py - Category-specific (browser, desktop)</category>
            <test_file>Top of test file - Test-specific fixtures</test_file>
          </fixture_placement>
        </organization>

        <decision_tree name="Create new fixture?">
          <question>Used in 3+ test files?</question>
          <yes>
            <question>Specific to category (browser/desktop)?</question>
            <yes>Place in tests/&lt;category&gt;/conftest.py</yes>
            <no>Place in tests/conftest.py</no>
          </yes>
          <no>
            <question>Used in 2+ tests in same file?</question>
            <yes>Fixture at top of test file</yes>
            <no>Inline in test (no fixture needed)</no>
          </no>
        </decision_tree>
      </test_structure>

      <quality_standards>
        <assertions>
          <rule>One logical assertion per test (multiple asserts OK if same concept).</rule>
          <rule>Assert on BEHAVIOR, not implementation.</rule>
          <rule>Use descriptive assertion messages for complex checks.</rule>

          <good>
            # Clear, behavioral assertions
            assert result.status == ExecutionStatus.COMPLETED
            assert len(workflow.nodes) == 3
            assert "error" in result, "Error should be present in failed result"
          </good>

          <bad>
            # Implementation-focused assertions
            assert workflow._nodes_dict["node1"] is not None  # Testing internals
            assert mock.call_count == 1  # Brittle, use assert_called_once()
          </bad>
        </assertions>

        <isolation>
          <rule>Tests must be independent (order doesn't matter).</rule>
          <rule>No shared state between tests.</rule>
          <rule>Use fixtures for setup, not setUp/tearDown methods.</rule>
          <rule>Reset mocks between tests (pytest does this automatically).</rule>
        </isolation>

        <avoid_flaky>
          <async_timing>
            # Bad: Hard-coded sleep
            await asyncio.sleep(1)  # Flaky, slow

            # Good: Wait for condition
            await wait_for_condition(lambda: resource.is_ready(), timeout=5)
          </async_timing>

          <qt_events>
            # Bad: Process events without limit
            qtbot.wait(1000)  # Arbitrary wait

            # Good: Wait for signal
            with qtbot.waitSignal(widget.signal_name, timeout=1000):
                widget.trigger_action()
          </qt_events>
        </avoid_flaky>
      </quality_standards>

      <ci_integration>
        <commands>
          <local>pytest tests/ -v</local>
          <coverage>pytest tests/ -v --cov=casare_rpa --cov-report=term --cov-report=html</coverage>
          <fast>pytest tests/ -v -m "not slow"</fast>
          <specific>pytest tests/domain/ -v</specific>
        </commands>

        <markers>
          <slow desc="Long-running tests (integration, E2E)">@pytest.mark.slow</slow>
          <integration desc="Integration tests">@pytest.mark.integration</integration>
          <e2e desc="End-to-end tests">@pytest.mark.e2e</e2e>
        </markers>

        <coverage_targets>
          <domain>90%+ (pure logic, easy to test)</domain>
          <application>85%+ (use case orchestration)</application>
          <infrastructure>70%+ (adapters, mocked externals)</infrastructure>
          <presentation>50%+ (Qt complexity, minimal testing)</presentation>
          <nodes>80%+ (core automation logic)</nodes>
        </coverage_targets>

        <github_actions file=".github/workflows/ci.yml">
          # Already configured:
          # - Python 3.12 on Windows
          # - pytest with coverage (--cov=casare_rpa)
          # - Coverage upload to Codecov
          # - Ruff linting (informational)
          # - MyPy type checking (informational)
        </github_actions>
      </ci_integration>

      <migration_testing>
        <v2_to_v3>
          <strategy>Test both old and new APIs during migration.</strategy>

          <characterization_tests>
            # Capture legacy behavior before refactoring
            def test_legacy_workflow_loader_behavior():
                """Characterization test for old WorkflowLoader API."""
                loader = LegacyWorkflowLoader()
                workflow = loader.load("path/to/workflow.json")

                # Document current behavior (even if weird)
                assert workflow.version == "2.0"
                assert len(workflow.nodes) == expected_count
          </characterization_tests>

          <parametrized_migration>
            # Test both implementations
            @pytest.mark.parametrize("loader_class", [
                LegacyWorkflowLoader,
                NewWorkflowLoader,
            ])
            def test_workflow_loading(loader_class):
                loader = loader_class()
                workflow = loader.load("test_workflow.json")

                assert workflow.name == "Test Workflow"
                # Same behavior, different implementation
          </parametrized_migration>
        </v2_to_v3>
      </migration_testing>

      <performance_testing>
        <when_to_write>
          <item>Critical path operations (workflow execution)</item>
          <item>Resource-intensive operations (browser contexts, image processing)</item>
          <item>Known performance issues being fixed</item>
          <item>Algorithms with O(n²) or worse complexity</item>
        </when_to_write>

        <example file="tests/performance/test_workflow_execution.py">
          @pytest.mark.slow
          def test_execute_100_node_workflow_under_1_second(benchmark):
              workflow = create_workflow_with_n_nodes(100)
              orchestrator = ExecutionOrchestrator()

              result = benchmark(orchestrator.execute, workflow)

              assert result.status == ExecutionStatus.COMPLETED
              assert benchmark.stats.median &lt; 1.0  # Under 1 second
        </example>
      </performance_testing>

      <decision_trees>
        <what_kind_of_test>
          <question>What am I testing?</question>
          <domain>
            <type>Unit test</type>
            <mocks>None (real domain objects)</mocks>
            <location>tests/domain/</location>
          </domain>
          <application>
            <type>Integration test</type>
            <mocks>Infrastructure only</mocks>
            <location>tests/application/</location>
          </application>
          <infrastructure>
            <type>Unit test with mocks</type>
            <mocks>All external APIs</mocks>
            <location>tests/infrastructure/ or tests/nodes/</location>
          </infrastructure>
          <presentation>
            <type>Controller test</type>
            <mocks>Heavy Qt components</mocks>
            <location>tests/presentation/</location>
          </presentation>
          <full_workflow>
            <type>E2E test</type>
            <mocks>Minimal (only external I/O)</mocks>
            <location>tests/integration/</location>
          </full_workflow>
        </what_kind_of_test>

        <mock_or_real>
          <question>Is it an external API?</question>
          <yes>ALWAYS MOCK</yes>
          <no>
            <question>Is it domain logic?</question>
            <yes>PREFER REAL</yes>
            <no>
              <question>Is it infrastructure?</question>
              <yes>CONTEXT DEPENDENT (mock if has external deps)</yes>
            </no>
          </no>
        </mock_or_real>
      </decision_trees>

      <quick_reference>
        <tdd_checklist>
          <step>☐ Write failing test (Red)</step>
          <step>☐ Run test, verify it fails: pytest path/to/test.py::test_name -v</step>
          <step>☐ Write minimal code (Green)</step>
          <step>☐ Run test, verify it passes</step>
          <step>☐ Refactor (if needed)</step>
          <step>☐ Run all tests: pytest tests/ -v</step>
          <step>☐ Commit: git add tests/ src/ &amp;&amp; git commit -m "..."</step>
        </tdd_checklist>

        <common_patterns>
          <domain_entity_test>
            def test_entity_behavior():
                entity = Entity(...)
                entity.do_something()
                assert entity.state == expected_state
          </domain_entity_test>

          <application_use_case_test>
            @pytest.mark.asyncio
            async def test_use_case(mocker):
                mock_repo = mocker.AsyncMock()
                use_case = UseCase(repository=mock_repo)

                result = await use_case.execute(...)

                assert result.success
                mock_repo.save.assert_awaited_once()
          </application_use_case_test>

          <node_test>
            @pytest.mark.asyncio
            async def test_node_execute(execution_context, mock_resource):
                node = SomeNode(param="value")
                execution_context.resources["key"] = mock_resource

                result = await node.execute(execution_context)

                assert result["success"] is True
          </node_test>
        </common_patterns>
      </quick_reference>
    </tdd>
  </project>
</context>
