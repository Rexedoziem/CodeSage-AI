import syn.types
import syn.types.a

#-------------------------------------------------------------------------------
# Types imports

def test_types_imports():
    assert syn.types.Type is syn.types.a.Type

#-------------------------------------------------------------------------------

if __name__ == '__main__': # pragma: no cover
    from syn.base_utils import run_all_tests
    run_all_tests(globals(), verbose=True, print_errors=False)
