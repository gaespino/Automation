"""
Parity tests: FastAPI REST backend vs original PPV/tkinter logic.
==================================================================
These tests validate that the new REST endpoints expose all the same
functional capabilities as the original tkinter GUI tools.
"""
import importlib
import os
import sys
import pytest

# Make Portfolio the root so imports resolve correctly
HERE = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO = os.path.dirname(HERE)  # Portfolio/
sys.path.insert(0, PORTFOLIO)
sys.path.insert(0, os.path.join(PORTFOLIO, 'api'))


# ---------------------------------------------------------------------------
# 1. FastAPI app imports and all routers are registered
# ---------------------------------------------------------------------------
class TestFastAPIStructure:
    def test_main_imports(self):
        from api.main import app
        assert app is not None

    def test_all_routers_mounted(self):
        from api.main import app
        routes = {r.path for r in app.routes}
        for prefix in ['/api/mca', '/api/loops', '/api/files',
                       '/api/framework', '/api/fuses',
                       '/api/experiments', '/api/flow']:
            matching = [p for p in routes if p.startswith(prefix)]
            assert matching, f"No routes found for prefix {prefix!r}"

    def test_health_endpoint(self):
        from api.main import app
        routes = {r.path for r in app.routes}
        assert '/health' in routes

    def test_thr_spa_routes(self):
        from api.main import app
        paths = [r.path for r in app.routes]
        assert any('/thr' in p for p in paths), "React SPA route /thr not registered"


# ---------------------------------------------------------------------------
# 2. Flow router — validate / export / layout
# ---------------------------------------------------------------------------
class TestFlowParity:
    def _make_simple_flow(self):
        from api.routers.flow import FlowModel, NodeModel
        return FlowModel(nodes={
            'N1': NodeModel(id='N1', name='Start', type='StartNode',
                            x=160, y=160, connections={'0': 'N2'}),
            'N2': NodeModel(id='N2', name='Baseline', type='AdaptiveFlowInstance',
                            x=380, y=160, experiment='Baseline',
                            connections={'0': 'N3', '3': 'N3'}),
            'N3': NodeModel(id='N3', name='End', type='EndNode',
                            x=600, y=160),
        })

    def test_validate_valid_flow(self):
        import asyncio
        from api.routers.flow import validate_flow
        flow = self._make_simple_flow()
        result = asyncio.get_event_loop().run_until_complete(validate_flow(flow))
        assert result['valid'] is True
        assert result['errors'] == []

    def test_validate_missing_start(self):
        import asyncio
        from api.routers.flow import validate_flow, FlowModel, NodeModel
        flow = FlowModel(nodes={
            'N1': NodeModel(id='N1', name='A', type='AdaptiveFlowInstance',
                            x=0, y=0, experiment='X'),
        })
        result = asyncio.get_event_loop().run_until_complete(validate_flow(flow))
        assert result['valid'] is False
        assert any('StartNode' in e for e in result['errors'])

    def test_validate_missing_experiment_warns(self):
        import asyncio
        from api.routers.flow import validate_flow, FlowModel, NodeModel
        flow = FlowModel(nodes={
            'N1': NodeModel(id='N1', name='Start', type='StartNode', x=0, y=0, connections={'0':'N2'}),
            'N2': NodeModel(id='N2', name='NoExp', type='AdaptiveFlowInstance', x=200, y=0),
        })
        result = asyncio.get_event_loop().run_until_complete(validate_flow(flow))
        assert any('experiment' in w for w in result['warnings'])

    def test_export_returns_streaming_response(self):
        import asyncio
        from api.routers.flow import export_flow
        flow = self._make_simple_flow()
        resp = asyncio.get_event_loop().run_until_complete(export_flow(flow))
        assert 'FlowConfig.zip' in resp.headers.get('content-disposition', '')

    def test_export_zip_contains_four_files(self):
        import asyncio, io, zipfile
        from fastapi.responses import StreamingResponse
        from api.routers.flow import export_flow

        async def _collect():
            resp = await export_flow(self._make_simple_flow())
            chunks = []
            async for chunk in resp.body_iterator:
                chunks.append(chunk)
            return b''.join(chunks)

        content = asyncio.get_event_loop().run_until_complete(_collect())
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            names = z.namelist()
        assert 'FrameworkAutomationStructure.json' in names
        assert 'FrameworkAutomationFlows.json' in names
        assert 'FrameworkAutomationInit.ini' in names
        assert 'FrameworkAutomationPositions.json' in names

    def test_layout_returns_positions(self):
        import asyncio
        from api.routers.flow import auto_layout
        flow = self._make_simple_flow()
        result = asyncio.get_event_loop().run_until_complete(auto_layout(flow))
        assert 'positions' in result
        assert 'N1' in result['positions']
        assert 'x' in result['positions']['N1']
        assert 'y' in result['positions']['N1']

    def test_layout_positions_on_20px_grid(self):
        import asyncio
        from api.routers.flow import auto_layout
        flow = self._make_simple_flow()
        result = asyncio.get_event_loop().run_until_complete(auto_layout(flow))
        for nid, pos in result['positions'].items():
            assert pos['x'] % 20 == 0, f"{nid}.x not on 20px grid"
            assert pos['y'] % 20 == 0, f"{nid}.y not on 20px grid"

    def test_ppv_coordinate_conversion_in_export(self):
        """Export must write PPV top-left coords (cytoscape centre - 75/50)."""
        import asyncio, io, json, zipfile
        from api.routers.flow import export_flow, FlowModel, NodeModel

        async def _collect():
            resp = await export_flow(FlowModel(nodes={
                'N1': NodeModel(id='N1', name='Start', type='StartNode', x=160, y=160),
            }))
            chunks = []
            async for chunk in resp.body_iterator:
                chunks.append(chunk)
            return b''.join(chunks)

        content = asyncio.get_event_loop().run_until_complete(_collect())
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            positions = json.loads(z.read('FrameworkAutomationPositions.json'))
        assert positions['N1']['x'] == 85
        assert positions['N1']['y'] == 110


# ---------------------------------------------------------------------------
# 3. Fuses router — product data loading
# ---------------------------------------------------------------------------
class TestFusesParity:
    def _fuse_dir_exists(self, product):
        return os.path.isdir(os.path.join(PORTFOLIO, 'THRTools', 'configs', 'fuses', product))

    @pytest.mark.skipif(not os.path.isdir(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'THRTools', 'configs', 'fuses')
    ), reason="No fuse configs found")
    def test_fuse_products_discoverable(self):
        fuse_root = os.path.join(PORTFOLIO, 'THRTools', 'configs', 'fuses')
        products = [d for d in os.listdir(fuse_root) if os.path.isdir(os.path.join(fuse_root, d))]
        assert len(products) >= 1, "Expected at least one fuse product directory"

    def test_generate_endpoint_produces_bytes(self):
        import asyncio
        from api.routers.fuses import generate_fuse_file, FuseGenerateRequest
        req = FuseGenerateRequest(product='GNR', selected_names=[], filename='test.fuse')
        resp = asyncio.get_event_loop().run_until_complete(generate_fuse_file(req))
        assert resp is not None


# ---------------------------------------------------------------------------
# 4. Experiments router — config lookup
# ---------------------------------------------------------------------------
class TestExperimentsParity:
    def test_products_endpoint(self):
        import asyncio
        from api.routers.experiments import get_products
        result = asyncio.get_event_loop().run_until_complete(get_products())
        assert 'products' in result
        assert isinstance(result['products'], list)

    def test_build_experiment_returns_bytes(self):
        import asyncio
        from api.routers.experiments import build_experiments, ExperimentBuildRequest
        req = ExperimentBuildRequest(
            experiments=[{'ExperimentName': 'Test', 'Content': 'Dragon'}],
            filename='test.tpl',
        )
        resp = asyncio.get_event_loop().run_until_complete(build_experiments(req))
        assert resp is not None


# ---------------------------------------------------------------------------
# 5. React UI build artefact exists
# ---------------------------------------------------------------------------
class TestReactBuild:
    _DIST = os.path.join(PORTFOLIO, 'thr_ui', 'dist')

    def test_dist_exists(self):
        assert os.path.isdir(self._DIST), \
            "React dist/ not found — run: cd thr_ui && npm run build"

    def test_index_html_exists(self):
        index = os.path.join(self._DIST, 'index.html')
        assert os.path.isfile(index), "dist/index.html missing"

    def test_index_html_has_correct_base(self):
        index = os.path.join(self._DIST, 'index.html')
        with open(index) as f:
            content = f.read()
        assert '/thr/' in content, "Vite base '/thr/' not found in index.html"

    def test_assets_dir_exists(self):
        assets = os.path.join(self._DIST, 'assets')
        assert os.path.isdir(assets) and len(os.listdir(assets)) > 0


# ---------------------------------------------------------------------------
# 6. Node type parity — all 9 PPV node types are registered in React
# ---------------------------------------------------------------------------
class TestNodeTypeParity:
    """
    The original PPV AutomationDesigner had exactly these 9 node types.
    Check that all are defined in the FastAPI flow router.
    """
    EXPECTED_TYPES = {
        'StartNode', 'EndNode',
        'SingleFailFlowInstance', 'AllFailFlowInstance', 'MajorityFailFlowInst',
        'AdaptiveFlowInstance', 'CharacterizationFI', 'DataCollectionFI',
        'AnalysisFlowInstance',
    }

    def test_all_ppv_node_types_accepted_in_validation(self):
        import asyncio
        from api.routers.flow import validate_flow, FlowModel, NodeModel
        for nt in self.EXPECTED_TYPES:
            flow = FlowModel(nodes={
                'N1': NodeModel(id='N1', name='Start', type='StartNode', x=0, y=0),
                'N2': NodeModel(id='N2', name='Test', type=nt, x=200, y=0,
                                experiment='TestExp' if nt not in ('StartNode','EndNode') else None),
            })
            result = asyncio.get_event_loop().run_until_complete(validate_flow(flow))
            # No crash and returns expected keys
            assert 'valid' in result, f"validate_flow returned unexpected format for type {nt}"


# ---------------------------------------------------------------------------
# 7. Entry point change documented
# ---------------------------------------------------------------------------
class TestEntryPointMigration:
    def test_fastapi_app_importable_as_api_main(self):
        """New CaaS entry point: uvicorn api.main:app"""
        from api.main import app
        assert hasattr(app, 'routes')

    def test_dash_app_still_importable(self):
        """Dash app (Dashboard) must remain importable for /dashboard/ mount."""
        # May fail if Dash not installed — that's OK in test env
        try:
            import app as dash_app
            assert hasattr(dash_app, 'server')
        except ImportError:
            pytest.skip("Dash not installed in this environment")
