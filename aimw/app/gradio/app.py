import gradio as gr

from app.gradio.generation import convert_and_cache_pdf, run_compliance_check

css = """
#submit-button {
    background-color: #7030A0;
    color: white;
    border: none;
    height: 40px;
    margin-left: 10px;
}
#input-text {
    flex-grow: 1;
}
#agent-thinking-output {
    min-height: 750px;
    max-height: 750px;
    overflow-y: auto;
    resize: none;
}
#final-answer-output {
    min-height: 750px;
    max-height: 750px;
    overflow-y: auto;
    resize: none;
}
footer, .svelte-13fuv1y, .svelte-1ipelgc { display: none !important; }
"""


with gr.Blocks(css=css, title="PDF Agent QA") as demo:
    cached_markdown = gr.State(None)

    # === TOP ROW: Upload controls centered and spanning ===
    with gr.Row():
        file_input = gr.File(
            label="Upload PDF file",
            file_types=[".pdf"],
            type="filepath",
            visible=True,
            scale=6,
        )
    process_pdf_btn = gr.Button("Process PDF", visible=True, scale=1)

    # === MIDDLE ROW: Answer panels ===
    with gr.Row():
        with gr.Column(scale=3):
            final_answer_output = gr.Markdown(
                "",
                elem_id="final-answer-output",
                min_height=750,
                show_copy_button=True,
                container=True,
                label="Final Answer",
            )
        with gr.Column(scale=1):
            thinking_output = gr.Markdown(
                "",
                elem_id="agent-thinking-output",
                min_height=750,
                show_copy_button=False,
                container=True,
                label="Agent Thinking",
            )

    # === QUESTION INPUT ROW (bottom) ===
    with gr.Row():
        input_text = gr.Textbox(
            placeholder="Type your question here...",
            lines=1,
            elem_id="input-text",
            show_label=False,
            container=False,
            scale=9,
            interactive=False,
        )
        submit_btn = gr.Button(
            "Send", elem_id="submit-button", scale=1, interactive=False
        )

    upload_again_btn = gr.Button("Upload Another PDF", visible=False)

    # ==== Process PDF logic ====
    def process_pdf_ui(file):
        if not file:
            return (
                gr.update(interactive=True),  # input_text
                gr.update(interactive=False),  # submit_btn
                None,  # cached_markdown
                "",  # final_answer_output
                "",  # thinking_output
                gr.Warning("Please upload a file first."),
                gr.update(visible=True),  # file_input
                gr.update(visible=True),  # process_pdf_btn
                gr.update(visible=False),  # upload_again_btn
            )
        markdown = convert_and_cache_pdf(file)
        return (
            gr.update(interactive=True),  # Enable textbox
            gr.update(interactive=True),  # Enable send button
            markdown,  # Store markdown in state
            "",  # Clear final answer panel
            "",  # Clear agent thinking panel
            gr.Info("PDF processed! Now ask a question.", duration=3),
            gr.update(visible=True),  # Hide file input
            gr.update(visible=False),  # Hide process button
            gr.update(visible=True),  # Show reset/upload again button
        )

    process_pdf_btn.click(
        fn=process_pdf_ui,
        inputs=[file_input],
        outputs=[
            input_text,  # 0
            submit_btn,  # 1
            cached_markdown,  # 2
            final_answer_output,  # 3
            thinking_output,  # 4
            gr.State(),  # 5 (banner, not used directly)
            file_input,  # 6 (to hide)
            process_pdf_btn,  # 7 (to hide)
            upload_again_btn,  # 8 (to show)
        ],
    )

    submit_btn.click(
        fn=run_compliance_check,
        inputs=[cached_markdown, input_text],
        outputs=[final_answer_output, thinking_output, input_text],
    )
    input_text.submit(
        fn=run_compliance_check,
        inputs=[cached_markdown, input_text],
        outputs=[final_answer_output, thinking_output, input_text],
    )

    def reset_workflow():
        return (
            None,  # cached_markdown
            "",  # final_answer_output
            "",  # thinking_output
            "",  # input_text
            gr.update(visible=True),  # file_input
            gr.update(visible=True),  # process_pdf_btn
            gr.update(visible=False),  # upload_again_btn
            gr.Info("Ready to upload a new PDF.", duration=2),
        )

    upload_again_btn.click(
        fn=reset_workflow,
        inputs=[],
        outputs=[
            cached_markdown,
            final_answer_output,
            thinking_output,
            input_text,
            file_input,
            process_pdf_btn,
            upload_again_btn,
            gr.State(),  # banner
        ],
    )

demo.queue().launch(server_name="0.0.0.0", share=False)
