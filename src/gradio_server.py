import gradio as gr  # 导入gradio库用于创建GUI

from config import Config  # 导入配置管理模块
from github_client import GitHubClient  # 导入用于GitHub API操作的客户端
from report_generator import ReportGenerator  # 导入报告生成器模块
from llm import LLM  # 导入可能用于处理语言模型的LLM类
from subscription_manager import SubscriptionManager  # 导入订阅管理器
from logger import LOG  # 导入日志记录器

# 创建各个组件的实例
config = Config()
github_client = GitHubClient(config.github_token)
llm = LLM()
report_generator = ReportGenerator(llm)
subscription_manager = SubscriptionManager(config.subscriptions_file)

# Updated functions to add and delete items using SubscriptionManager
def add_subscription(repo, subscriptions):
    subscription_manager.add_subscription(repo)
    updated_subscriptions = subscription_manager.list_subscriptions()
    return gr.Dropdown(choices=updated_subscriptions), ""

def delete_subscription(repo, subscriptions):
    subscription_manager.remove_subscription(repo)
    updated_subscriptions = subscription_manager.list_subscriptions()
    return gr.Dropdown(choices=updated_subscriptions)

# Updated functions to add and delete items using SubscriptionManager
def manage_subscriptions(action, repo, subscriptions):
    if action == "Add":
        subscription_manager.add_subscription(repo)
    elif action == "Delete":
        subscription_manager.remove_subscription(repo)
    
    # Return the updated list of subscriptions
    return subscription_manager.list_subscriptions()

def export_progress_by_date_range(repo, days):
    # 定义一个函数，用于导出和生成指定时间范围内项目的进展报告
    raw_file_path = github_client.export_progress_by_date_range(repo, days)  # 导出原始数据文件路径
    report, report_file_path = report_generator.generate_report_by_date_range(raw_file_path, days)  # 生成并获取报告内容及文件路径

    return report, report_file_path  # 返回报告内容和报告文件路径
    
# 创建Gradio界面
with gr.Blocks() as demo:
    gr.Markdown("# GitHub Sentinel")
    
    # Add Subscription Area
    with gr.Row():
        repo_input = gr.Textbox(label="Enter GitHub Project Name", placeholder="Enter for 'Add' action", scale=4)
        add_button = gr.Button("Add", scale=1)  # Adjust button width using scale

    subscriptions_state = gr.State(subscription_manager.list_subscriptions())

    # Delete Subscription Area
    with gr.Row():
        dropdown = gr.Dropdown(choices=subscription_manager.list_subscriptions(),
                               label="訂閱列表", info="已訂閱GitHub專案",multiselect=False, scale=4)
        delete_button = gr.Button("Delete", scale=1)  # Adjust button width using scale
    
    report_period = gr.Slider(value=2, minimum=1, maximum=7, step=1, label="報告涵蓋天數",
                              info="生成專案過去一段時間進展，單位：天")
    
    report_output = gr.Markdown()
    file_output = gr.File(label="下載報告")

    add_button.click(fn=add_subscription, inputs=[repo_input, subscriptions_state], outputs=[dropdown, repo_input])
    delete_button.click(fn=delete_subscription, inputs=[dropdown, subscriptions_state], outputs=[dropdown])

    repo_input.submit(fn=export_progress_by_date_range, inputs=[dropdown, report_period], outputs=[report_output, file_output])

    # Add a button to trigger the action
    submit_button = gr.Button("產生選定專案的變動摘要報告")    
    submit_button.click(
        fn=export_progress_by_date_range,
        inputs=[dropdown, report_period],
        outputs=[report_output, file_output]
    )

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0")  # 启动界面并设置为公共可访问
    # 可选带有用户认证的启动方式
    # demo.launch(share=True, server_name="0.0.0.0", auth=("django", "1234"))