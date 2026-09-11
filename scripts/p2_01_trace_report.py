"""Compatibility entry point for the original P2-01 trace report."""
import sys
from jump_trace_report import main
if __name__=='__main__':
 sys.argv=[sys.argv[0],'configs/reports/p2-01.json'];main()
