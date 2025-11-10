import sys
from pathlib import Path
from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit
agent_dir = Path(__file__).parent  
if str(agent_dir) not in sys.path:  
    sys.path.insert(0, str(agent_dir))  
    
import my_actions.my_action
import my_recognitions.my_reco
import my_recognitions.圣石选择


def main():
    Toolkit.init_option("./")

    socket_id = sys.argv[-1]

    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()